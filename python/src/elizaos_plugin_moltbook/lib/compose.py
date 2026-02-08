"""
Content Composition with LLM

Generates posts and comments with quality gating.

Python port of TypeScript compose from plugin-moltbook/typescript/src/lib/compose.ts
"""

import json
import logging
from typing import Any, Dict, List, Optional
from ..types import MoltbookPost, MoltbookComment, ContentToJudge
from ..constants import MAX_COMPOSE_RETRIES
from .templates import get_post_template, get_comment_template
from .judge import judge_content

logger = logging.getLogger(__name__)


async def compose_post(
    character_name: str,
    character_bio: str,
    submolt: Optional[str],
    recent_posts: List[MoltbookPost],
    topics: List[str],
    min_quality: int,
    llm_generate_fn: Any  # Function that calls LLM
) -> Optional[Dict[str, str]]:
    """
    Compose a post with quality gating
    
    Args:
        character_name: Agent's name
        character_bio: Agent's bio/personality
        submolt: Target submolt (community)
        recent_posts: Recent posts for context
        topics: Hot topics
        min_quality: Minimum quality score (1-10)
        llm_generate_fn: Async function that calls LLM with a prompt
    
    Returns:
        Dict with 'title' and 'content' if successful, None otherwise
    """
    
    prompt = get_post_template(
        character_name=character_name,
        character_bio=character_bio,
        submolt=submolt,
        recent_posts=recent_posts,
        topics=topics
    )
    
    for attempt in range(MAX_COMPOSE_RETRIES):
        try:
            logger.debug(f"Composing post (attempt {attempt + 1}/{MAX_COMPOSE_RETRIES})")
            
            # Generate content with LLM
            response = await llm_generate_fn(prompt)
            
            # Parse JSON response
            try:
                result = json.loads(response)
                title = result.get('title', '').strip()
                content = result.get('content', '').strip()
                
                if not title or not content:
                    logger.warning(f"Empty title or content on attempt {attempt + 1}")
                    continue
                
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON response on attempt {attempt + 1}")
                continue
            
            # Judge quality
            context = f"Posting in '{submolt or 'general'}' about: {', '.join(topics)}"
            content_to_judge = ContentToJudge(
                title=title,
                content=content,
                context=context,
                isComment=False
            )
            
            quality = await judge_content(
                content_to_judge=content_to_judge,
                llm_generate_fn=llm_generate_fn
            )
            
            if quality and quality.overall >= min_quality:
                logger.info(f"Post composed successfully (quality: {quality.overall}/10)")
                return {'title': title, 'content': content}
            
            logger.info(f"Quality too low ({quality.overall if quality else 0}/10), retrying...")
            
        except Exception as e:
            logger.error(f"Error composing post: {e}")
            continue
    
    logger.warning(f"Failed to compose post after {MAX_COMPOSE_RETRIES} attempts")
    return None


async def compose_comment(
    character_name: str,
    character_bio: str,
    post: MoltbookPost,
    parent_comment: Optional[MoltbookComment],
    min_quality: int,
    llm_generate_fn: Any
) -> Optional[str]:
    """
    Compose a comment with quality gating
    
    Args:
        character_name: Agent's name
        character_bio: Agent's bio/personality
        post: Post being commented on
        parent_comment: Parent comment if replying
        min_quality: Minimum quality score (1-10)
        llm_generate_fn: Async function that calls LLM with a prompt
    
    Returns:
        Comment content if successful, None otherwise
    """
    
    prompt = get_comment_template(
        character_name=character_name,
        character_bio=character_bio,
        post=post,
        parent_comment=parent_comment
    )
    
    for attempt in range(MAX_COMPOSE_RETRIES):
        try:
            logger.debug(f"Composing comment (attempt {attempt + 1}/{MAX_COMPOSE_RETRIES})")
            
            # Generate content with LLM
            response = await llm_generate_fn(prompt)
            
            # Parse JSON response
            try:
                result = json.loads(response)
                content = result.get('content', '').strip()
                
                if not content:
                    logger.warning(f"Empty content on attempt {attempt + 1}")
                    continue
                
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON response on attempt {attempt + 1}")
                continue
            
            # Judge quality
            context = f"Commenting on: \"{post.get('title', '')}\" by {post.get('author', {}).get('username', 'unknown')}"
            content_to_judge = ContentToJudge(
                content=content,
                context=context,
                isComment=True
            )
            
            quality = await judge_content(
                content_to_judge=content_to_judge,
                llm_generate_fn=llm_generate_fn
            )
            
            if quality and quality.overall >= min_quality:
                logger.info(f"Comment composed successfully (quality: {quality.overall}/10)")
                return content
            
            logger.info(f"Quality too low ({quality.overall if quality else 0}/10), retrying...")
            
        except Exception as e:
            logger.error(f"Error composing comment: {e}")
            continue
    
    logger.warning(f"Failed to compose comment after {MAX_COMPOSE_RETRIES} attempts")
    return None
