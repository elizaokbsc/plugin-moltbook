"""
Community Intelligence and Analysis

Analyzes community to find engagement opportunities.

Python port of TypeScript intelligence from plugin-moltbook/typescript/src/lib/intelligence.ts
"""

import json
import logging
from typing import Any, List, Optional
from ..types import CommunityContext, EngagementOpportunity, MoltbookPost, MoltbookProfile
from .templates import get_community_analysis_template

logger = logging.getLogger(__name__)


async def analyze_community(
    posts: List[MoltbookPost],
    character_name: str,
    llm_generate_fn: Any
) -> Optional[CommunityContext]:
    """
    Analyze community to understand trends and find engagement opportunities
    
    Args:
        posts: Recent posts to analyze
        character_name: Agent's name for personalized analysis
        llm_generate_fn: Async function that calls LLM with a prompt
    
    Returns:
        CommunityContext if successful, None otherwise
    """
    
    if not posts:
        logger.warning("No posts to analyze")
        return None
    
    prompt = get_community_analysis_template(
        posts=posts,
        character_name=character_name
    )
    
    try:
        logger.debug(f"Analyzing community ({len(posts)} posts)")
        
        # Get LLM analysis
        response = await llm_generate_fn(prompt)
        
        # Parse JSON response
        try:
            result = json.loads(response)
            
            active_topics = result.get('activeTopics', [])
            vibe = result.get('vibe', 'Unknown')
            what_works = result.get('whatWorks', [])
            engagement_opps_data = result.get('engagementOpportunities', [])
            
            # Parse engagement opportunities
            engagement_opportunities = []
            for opp in engagement_opps_data:
                post_id = opp.get('postId')
                # Find the post
                matching_post = next((p for p in posts if p.get('id') == post_id), None)
                if matching_post:
                    engagement_opportunities.append(
                        EngagementOpportunity(
                            post=matching_post,
                            reason=opp.get('reason', ''),
                            type=opp.get('type', 'comment'),
                            priority=opp.get('priority', 5)
                        )
                    )
            
            # Sort by priority (highest first)
            engagement_opportunities.sort(key=lambda x: x.priority, reverse=True)
            
            # Extract notable community members from posts
            notable_moltys: List[MoltbookProfile] = []
            seen_users = set()
            for post in posts:
                author = post.get('author')
                if author and author.get('username') not in seen_users:
                    notable_moltys.append(author)
                    seen_users.add(author.get('username'))
                if len(notable_moltys) >= 5:
                    break
            
            context = CommunityContext(
                activeTopics=active_topics,
                engagementOpportunities=engagement_opportunities,
                whatWorks=what_works,
                notableMoltys=notable_moltys,
                vibe=vibe,
                analyzedAt=int(__import__('time').time() * 1000)
            )
            
            logger.info(f"Community analyzed: {len(active_topics)} topics, {len(engagement_opportunities)} opportunities")
            return context
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse community analysis: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Error analyzing community: {e}")
        return None


def find_engagement_opportunities(
    posts: List[MoltbookPost],
    character_interests: List[str]
) -> List[EngagementOpportunity]:
    """
    Simple heuristic-based engagement opportunity finder
    (backup when LLM analysis isn't available)
    
    Args:
        posts: Posts to analyze
        character_interests: Topics the agent is interested in
    
    Returns:
        List of engagement opportunities
    """
    
    opportunities = []
    
    for post in posts:
        title = post.get('title', '').lower()
        content = post.get('content', '').lower()
        score = post.get('score', 0)
        comment_count = post.get('commentCount', 0)
        
        # Calculate priority based on engagement and relevance
        priority = 5
        reason_parts = []
        
        # High engagement = interesting to community
        if score > 10:
            priority += 2
            reason_parts.append("high engagement")
        
        # Few comments = opportunity to add value
        if comment_count < 5:
            priority += 1
            reason_parts.append("open discussion")
        
        # Matches interests
        for interest in character_interests:
            if interest.lower() in title or interest.lower() in content:
                priority += 3
                reason_parts.append(f"relevant to {interest}")
                break
        
        if priority > 5:  # Only include if priority increased
            opportunities.append(
                EngagementOpportunity(
                    post=post,
                    reason=", ".join(reason_parts) if reason_parts else "potential engagement",
                    type='comment',
                    priority=min(priority, 10)
                )
            )
    
    # Sort by priority
    opportunities.sort(key=lambda x: x.priority, reverse=True)
    
    return opportunities[:10]  # Top 10


def format_community_context(context: CommunityContext) -> str:
    """Format community context into human-readable string"""
    
    lines = [
        "## Community Analysis",
        "",
        f"**Vibe**: {context.vibe}",
        "",
        "**Hot Topics**:",
    ]
    
    for topic in context.activeTopics:
        lines.append(f"- {topic}")
    
    lines.extend(["", "**What Works**:"])
    for pattern in context.whatWorks:
        lines.append(f"- {pattern}")
    
    lines.extend(["", f"**Engagement Opportunities**: {len(context.engagementOpportunities)}"])
    for i, opp in enumerate(context.engagementOpportunities[:5], 1):
        post_title = opp.post.get('title', 'Unknown')
        lines.append(f"{i}. [{opp.priority}/10] {post_title[:60]}... - {opp.reason}")
    
    return "\n".join(lines)
