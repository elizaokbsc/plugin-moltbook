"""
Context Provider

Provides community context and analysis for agent decision-making.

Python port of TypeScript context provider
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def get_moltbook_context(runtime: Any, message: Any, state: Optional[Any] = None) -> str:
    """
    Provide community context to the agent
    
    Returns formatted context string with:
    - Authentication status
    - Rate limit status  
    - Community analysis (if available)
    - Engagement opportunities
    """
    try:
        service = runtime.get_service('moltbook')
        if not service:
            return "Moltbook service not available."
        
        lines = ["## Moltbook Context", ""]
        
        # Auth status
        creds = await service.get_credentials()
        if creds:
            username = creds.get('username', 'Unknown')
            claim_status = creds.get('claim_status', 'unclaimed')
            lines.append(f"**Status**: Authenticated as @{username} ({claim_status})")
        else:
            lines.append("**Status**: Not authenticated")
            return "\n".join(lines)
        
        # Rate limits
        from ..lib.rateLimiter import get_rate_limit_status
        limits = get_rate_limit_status(str(runtime.agent_id))
        
        can_post = "✓" if limits['can_post'] else "✗"
        can_comment = "✓" if limits['can_comment'] else "✗"
        
        lines.extend([
            "",
            f"**Can Post**: {can_post}",
            f"**Can Comment**: {can_comment}",
            f"**Requests Remaining**: {limits['requests_remaining']}/100 per minute",
            f"**Comments Remaining**: {limits['comments_remaining']}/50 per hour",
        ])
        
        if limits['time_until_can_post'] > 0:
            minutes = limits['time_until_can_post'] // 60000
            lines.append(f"**Next Post**: {minutes}m")
        
        # Community analysis (if cached)
        if hasattr(service, 'community_context') and service.community_context:
            context = service.community_context
            lines.extend([
                "",
                "## Community Intel",
                f"**Vibe**: {context.vibe}",
                "",
                "**Hot Topics**:",
            ])
            
            for topic in context.activeTopics[:5]:
                lines.append(f"- {topic}")
            
            if context.engagementOpportunities:
                lines.extend(["", "**Top Opportunities**:"])
                for i, opp in enumerate(context.engagementOpportunities[:3], 1):
                    post_title = opp.post.get('title', 'Unknown')[:50]
                    lines.append(f"{i}. [{opp.priority}/10] {post_title}... - {opp.reason}")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Error getting Moltbook context: {e}")
        return f"Error retrieving Moltbook context: {str(e)}"


# Provider definition for plugin registration
MOLTBOOK_CONTEXT_PROVIDER = {
    'name': 'moltbookContext',
    'description': 'Provides Moltbook community context and status',
    'get': get_moltbook_context
}
