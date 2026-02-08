"""
Autonomous Engagement Cycle Task

Periodically analyzes community and engages autonomously.

Python port of TypeScript cycle task
"""

import asyncio
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def run_cycle(runtime: Any, state: Optional[Any] = None) -> None:
    """
    Run one cycle of autonomous engagement
    
    1. Refresh community context
    2. Analyze for engagement opportunities
    3. Maybe post or comment (if auto-engage enabled)
    """
    try:
        service = runtime.get_service('moltbook')
        if not service:
            logger.warning("Moltbook service not available for cycle")
            return
        
        # Check if auto-engage is enabled
        auto_engage = runtime.get_setting('MOLTBOOK_AUTO_ENGAGE', 'false').lower() == 'true'
        
        logger.info(f"Running Moltbook cycle (auto-engage: {auto_engage})")
        
        # Get credentials
        creds = await service.get_credentials()
        if not creds:
            logger.warning("Not authenticated, skipping cycle")
            return
        
        # Fetch recent posts
        from ..lib.api import get_posts
        feed = await get_posts(
            agent_id=str(runtime.agent_id),
            api_key=creds['apiKey'],
            limit=20
        )
        
        if not feed or not feed.get('posts'):
            logger.info("No posts in feed")
            return
        
        posts = feed['posts']
        logger.debug(f"Fetched {len(posts)} posts")
        
        # Analyze community
        from ..lib.intelligence import analyze_community
        
        if hasattr(runtime, 'generate_text'):
            context = await analyze_community(
                posts=posts,
                character_name=runtime.character.name if hasattr(runtime, 'character') else "Agent",
                llm_generate_fn=runtime.generate_text
            )
            
            if context:
                # Store context in service for provider access
                service.community_context = context
                logger.info(f"Community analyzed: {len(context.activeTopics)} topics, {len(context.engagementOpportunities)} opportunities")
        
        # If auto-engage enabled, maybe engage
        if auto_engage:
            await _maybe_engage(runtime, service, creds, posts)
        
        logger.info("Cycle complete")
        
    except Exception as e:
        logger.error(f"Error in cycle task: {e}")


async def _maybe_engage(runtime: Any, service: Any, creds: dict, posts: list) -> None:
    """Maybe engage with community (post or comment)"""
    try:
        from ..lib.rateLimiter import can_post, can_comment
        from ..lib.intelligence import find_engagement_opportunities
        from ..constants import MIN_AUTONOMOUS_POST_INTERVAL_MS
        
        agent_id = str(runtime.agent_id)
        
        # Check if enough time has passed since last autonomous post
        if hasattr(service, 'last_autonomous_post_time'):
            elapsed = asyncio.get_event_loop().time() * 1000 - service.last_autonomous_post_time
            if elapsed < MIN_AUTONOMOUS_POST_INTERVAL_MS:
                logger.debug(f"Too soon for autonomous post ({elapsed/1000:.0f}s < {MIN_AUTONOMOUS_POST_INTERVAL_MS/1000:.0f}s)")
                return
        
        # Decide: post or comment?
        can_make_post = can_post(agent_id)
        can_make_comment = can_comment(agent_id)
        
        if not can_make_post and not can_make_comment:
            logger.debug("Rate limited for both posts and comments")
            return
        
        # Find opportunities using simple heuristics
        character_interests = []
        if hasattr(runtime, 'character') and hasattr(runtime.character, 'topics'):
            character_interests = runtime.character.topics
        
        opportunities = find_engagement_opportunities(posts, character_interests)
        
        if not opportunities:
            logger.debug("No engagement opportunities found")
            return
        
        # Take the top opportunity
        top_opp = opportunities[0]
        
        if top_opp.type == 'comment' and can_make_comment:
            logger.info(f"Attempting autonomous comment on: {top_opp.post.get('title', 'Unknown')[:50]}...")
            # Comment logic would go here
            # For now, just log
            logger.debug("Autonomous commenting not yet implemented in Python port")
        
        elif can_make_post:
            logger.info("Attempting autonomous post...")
            # Post logic would go here
            # For now, just log
            logger.debug("Autonomous posting not yet implemented in Python port")
            
            # Record time
            service.last_autonomous_post_time = asyncio.get_event_loop().time() * 1000
        
    except Exception as e:
        logger.error(f"Error in autonomous engagement: {e}")


# Task definition for plugin registration
CYCLE_TASK = {
    'name': 'MOLTBOOK_CYCLE',
    'description': 'Periodic community analysis and autonomous engagement',
    'handler': run_cycle,
    'interval_ms': 15 * 60 * 1000,  # 15 minutes
    'enabled': True
}
