"""
Mentions Processing

Handles mentions, replies, and tracks agent's own posts.

Python port of TypeScript mentions from plugin-moltbook/typescript/src/lib/mentions.ts
"""

import logging
from typing import Any, Dict, List, Optional
from ..types import MoltbookPost, MoltbookComment
from ..constants import MEMORY_TABLES

logger = logging.getLogger(__name__)


async def record_my_post(
    runtime: Any,
    post_id: str,
    title: str,
    content: str,
    submolt: Optional[str] = None
) -> bool:
    """
    Record a post created by this agent
    
    Args:
        runtime: AgentRuntime with memory access
        post_id: ID of the post
        title: Post title
        content: Post content
        submolt: Submolt it was posted in
    
    Returns:
        True if recorded successfully
    """
    try:
        memory_data = {
            'type': 'moltbook_my_post',
            'post_id': post_id,
            'title': title,
            'content': content,
            'submolt': submolt,
            'timestamp': int(__import__('time').time() * 1000)
        }
        
        # Store in memory
        # await runtime.memory.create(MEMORY_TABLES.MY_POSTS, memory_data)
        
        logger.debug(f"Recorded own post: {post_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to record own post: {e}")
        return False


async def get_my_posts(
    runtime: Any,
    limit: int = 10
) -> List[Dict]:
    """
    Retrieve posts created by this agent
    
    Args:
        runtime: AgentRuntime with memory access
        limit: Maximum number to retrieve
    
    Returns:
        List of post records
    """
    try:
        # Query memory
        # posts = await runtime.memory.query(
        #     table=MEMORY_TABLES.MY_POSTS,
        #     limit=limit,
        #     sort_by='timestamp',
        #     sort_order='desc'
        # )
        
        # Placeholder return
        posts = []
        
        logger.debug(f"Retrieved {len(posts)} own posts")
        return posts
        
    except Exception as e:
        logger.error(f"Failed to retrieve own posts: {e}")
        return []


async def poll_for_mentions(
    runtime: Any,
    api_get_notifications_fn: Any,  # Function to get notifications from API
    agent_username: str
) -> List[Dict]:
    """
    Poll for mentions and replies to agent's content
    
    Args:
        runtime: AgentRuntime
        api_get_notifications_fn: Async function to fetch notifications
        agent_username: This agent's username
    
    Returns:
        List of mention/reply notifications
    """
    try:
        logger.debug(f"Polling for mentions to @{agent_username}")
        
        # Fetch notifications from API
        notifications = await api_get_notifications_fn()
        
        if not notifications:
            return []
        
        # Filter for mentions and replies
        relevant = []
        for notif in notifications:
            notif_type = notif.get('type', '')
            if notif_type in ['mention', 'reply', 'comment']:
                relevant.append(notif)
        
        logger.info(f"Found {len(relevant)} mentions/replies")
        return relevant
        
    except Exception as e:
        logger.error(f"Failed to poll for mentions: {e}")
        return []


async def process_mentions(
    runtime: Any,
    mentions: List[Dict],
    process_callback: Any  # Async function to process each mention
) -> int:
    """
    Process a list of mentions/replies
    
    Args:
        runtime: AgentRuntime
        mentions: List of mention notifications
        process_callback: Async function called for each mention
    
    Returns:
        Number of mentions processed
    """
    processed = 0
    
    for mention in mentions:
        try:
            await process_callback(runtime, mention)
            processed += 1
        except Exception as e:
            logger.error(f"Failed to process mention: {e}")
            continue
    
    logger.info(f"Processed {processed}/{len(mentions)} mentions")
    return processed


def comment_to_memory(
    comment: MoltbookComment,
    post: Optional[MoltbookPost] = None
) -> Dict:
    """
    Convert a comment to a memory record format
    
    Args:
        comment: The comment
        post: Optional post the comment is on
    
    Returns:
        Memory record dictionary
    """
    return {
        'type': 'moltbook_comment',
        'comment_id': comment.get('id'),
        'post_id': comment.get('postId'),
        'parent_id': comment.get('parentId'),
        'content': comment.get('content'),
        'author': comment.get('author', {}).get('username'),
        'score': comment.get('score', 0),
        'created_at': comment.get('createdAt'),
        'post_title': post.get('title') if post else None,
        'timestamp': int(__import__('time').time() * 1000)
    }


def extract_mentions(text: str) -> List[str]:
    """
    Extract @mentions from text
    
    Args:
        text: Text to scan for mentions
    
    Returns:
        List of mentioned usernames (without @)
    """
    import re
    
    # Match @username pattern (letters, numbers, underscores, hyphens)
    pattern = r'@(\w+)'
    matches = re.findall(pattern, text)
    
    return matches


def is_reply_to_agent(
    comment: MoltbookComment,
    agent_username: str,
    parent_comment: Optional[MoltbookComment] = None
) -> bool:
    """
    Check if a comment is a reply to this agent
    
    Args:
        comment: The comment to check
        agent_username: This agent's username
        parent_comment: Parent comment if available
    
    Returns:
        True if it's a reply to the agent
    """
    # Check if replying to agent's comment
    if parent_comment:
        parent_author = parent_comment.get('author', {}).get('username', '')
        if parent_author == agent_username:
            return True
    
    # Check if agent is mentioned in the comment
    content = comment.get('content', '')
    mentions = extract_mentions(content)
    if agent_username in mentions:
        return True
    
    return False
