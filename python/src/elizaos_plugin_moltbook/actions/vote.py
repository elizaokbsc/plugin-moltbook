"""
Vote Action

Upvote or downvote posts and comments on Moltbook.

Python port of TypeScript vote action
"""

import re
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def extract_vote_intent(text: str) -> Dict[str, Any]:
    """Extract vote intent from message text"""
    text_lower = text.lower()
    
    # Determine vote type
    is_downvote = any(keyword in text_lower for keyword in ['downvote', 'down vote', 'thumbs down', '👎'])
    vote_type = 'down' if is_downvote else 'up'
    
    # Determine target type
    is_comment = 'comment' in text_lower
    target_type = 'comment' if is_comment else 'post'
    
    # Extract ID (look for common patterns)
    id_match = re.search(r'(?:id[:\s]+)?([a-f0-9]{8,})', text_lower)
    target_id = id_match.group(1) if id_match else None
    
    return {
        'vote_type': vote_type,
        'target_type': target_type,
        'target_id': target_id
    }


async def validate_vote_action(runtime: Any, message: Any, state: Optional[Any] = None) -> bool:
    """Validate if this is a vote action"""
    text = getattr(message.content, 'text', '') or str(message.content)
    text_lower = text.lower()
    
    # Check for vote intent
    has_vote_intent = any(keyword in text_lower for keyword in [
        'upvote', 'downvote', 'vote', 'up vote', 'down vote', 'thumbs up', 'thumbs down', '👍', '👎'
    ])
    
    has_moltbook_mention = any(keyword in text_lower for keyword in [
        'moltbook', 'molty', 'post', 'comment'
    ])
    
    return has_vote_intent and has_moltbook_mention


async def handle_vote_action(
    runtime: Any,
    message: Any,
    state: Optional[Any],
    options: Any,
    callback: Any
) -> Dict[str, Any]:
    """Handle vote action"""
    
    # Get service
    service = runtime.get_service('moltbook')
    if not service:
        error_msg = 'Moltbook service is not available'
        if callback:
            await callback({'text': error_msg, 'error': True})
        return {'success': False, 'error': error_msg}
    
    # Check authentication
    creds = await service.get_credentials()
    if not creds:
        error_msg = 'Not authenticated with Moltbook.'
        if callback:
            await callback({'text': error_msg, 'error': True})
        return {'success': False, 'error': error_msg}
    
    # Extract intent
    text = getattr(message.content, 'text', '') or str(message.content)
    intent = extract_vote_intent(text)
    
    if not intent['target_id']:
        error_msg = 'Please specify the post or comment ID to vote on.'
        if callback:
            await callback({'text': error_msg})
        return {'success': False, 'error': error_msg}
    
    try:
        target_id = intent['target_id']
        vote_type = intent['vote_type']
        target_type = intent['target_type']
        
        # Call appropriate API
        from ..lib.api import vote_post, vote_comment
        
        if target_type == 'comment':
            success = await vote_comment(
                agent_id=str(runtime.agent_id),
                api_key=creds['apiKey'],
                comment_id=target_id,
                vote=vote_type
            )
        else:
            success = await vote_post(
                agent_id=str(runtime.agent_id),
                api_key=creds['apiKey'],
                post_id=target_id,
                vote=vote_type
            )
        
        if success:
            vote_emoji = '👍' if vote_type == 'up' else '👎'
            result_text = f"{vote_emoji} {vote_type.capitalize()}voted {target_type} on Moltbook!"
            if callback:
                await callback({'text': result_text})
            logger.info(f"{vote_type.capitalize()}voted {target_type}: {target_id}")
            return {
                'success': True,
                'text': result_text,
                'data': {
                    'target_id': target_id,
                    'target_type': target_type,
                    'vote_type': vote_type
                }
            }
        else:
            error_msg = f"Failed to {vote_type}vote {target_type}"
            if callback:
                await callback({'text': error_msg, 'error': True})
            return {'success': False, 'error': error_msg}
            
    except Exception as e:
        error_msg = f"Error voting: {str(e)}"
        logger.error(error_msg)
        if callback:
            await callback({'text': error_msg, 'error': True})
        return {'success': False, 'error': error_msg}


# Action definition for plugin registration
VOTE_ACTION = {
    'name': 'MOLTBOOK_VOTE',
    'similes': ['UPVOTE_MOLTBOOK', 'DOWNVOTE_MOLTBOOK', 'MOLTBOOK_UPVOTE', 'MOLTBOOK_DOWNVOTE'],
    'description': 'Upvote or downvote posts and comments on Moltbook.',
    'validate': validate_vote_action,
    'handler': handle_vote_action
}
