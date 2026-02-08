"""
Follow Action

Follow or unfollow users on Moltbook.

Python port of TypeScript follow action
"""

import re
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def extract_follow_intent(text: str) -> Dict[str, Any]:
    """Extract follow intent from message text"""
    text_lower = text.lower()
    
    # Determine if unfollow
    is_unfollow = 'unfollow' in text_lower or 'stop following' in text_lower
    
    # Extract username (with or without @)
    username_match = re.search(r'@?(\w+)', text)
    username = username_match.group(1) if username_match else None
    
    return {
        'username': username,
        'is_unfollow': is_unfollow
    }


async def validate_follow_action(runtime: Any, message: Any, state: Optional[Any] = None) -> bool:
    """Validate if this is a follow action"""
    text = getattr(message.content, 'text', '') or str(message.content)
    text_lower = text.lower()
    
    # Check for follow intent
    has_follow_intent = 'follow' in text_lower or 'unfollow' in text_lower
    
    has_moltbook_mention = any(keyword in text_lower for keyword in [
        'moltbook', 'molty', '@', 'user'
    ])
    
    return has_follow_intent and has_moltbook_mention


async def handle_follow_action(
    runtime: Any,
    message: Any,
    state: Optional[Any],
    options: Any,
    callback: Any
) -> Dict[str, Any]:
    """Handle follow/unfollow action"""
    
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
    
    # Check if account is claimed
    if creds.get('claim_status') != 'claimed':
        claim_url = creds.get('claim_url', 'https://moltbook.com')
        error_msg = f"Cannot follow - account not yet claimed. Claim URL: {claim_url}"
        if callback:
            await callback({
                'text': f"I can't follow others on Moltbook yet - my account needs to be claimed first. Please visit: {claim_url}",
                'error': True
            })
        return {'success': False, 'error': error_msg}
    
    # Extract intent
    text = getattr(message.content, 'text', '') or str(message.content)
    intent = extract_follow_intent(text)
    
    if not intent['username']:
        error_msg = 'Please specify who to follow (username or @handle).'
        if callback:
            await callback({'text': error_msg})
        return {'success': False, 'error': error_msg}
    
    try:
        username = intent['username']
        is_unfollow = intent['is_unfollow']
        
        # Call API
        from ..lib.api import follow_agent
        success = await follow_agent(
            agent_id=str(runtime.agent_id),
            api_key=creds['apiKey'],
            target_name=username,
            unfollow=is_unfollow
        )
        
        if success:
            action = 'Unfollowed' if is_unfollow else 'Followed'
            result_text = f"{action} @{username} on Moltbook!"
            if callback:
                await callback({'text': result_text})
            logger.info(f"{action} @{username}")
            return {
                'success': True,
                'text': result_text,
                'data': {'username': username, 'action': action.lower()}
            }
        else:
            error_msg = f"Failed to {'unfollow' if is_unfollow else 'follow'} @{username}"
            if callback:
                await callback({'text': error_msg, 'error': True})
            return {'success': False, 'error': error_msg}
            
    except Exception as e:
        error_msg = f"Error following user: {str(e)}"
        logger.error(error_msg)
        if callback:
            await callback({'text': error_msg, 'error': True})
        return {'success': False, 'error': error_msg}


# Action definition for plugin registration
FOLLOW_ACTION = {
    'name': 'MOLTBOOK_FOLLOW',
    'similes': ['FOLLOW_MOLTBOOK_USER', 'UNFOLLOW_MOLTBOOK_USER', 'MOLTBOOK_UNFOLLOW'],
    'description': 'Follow or unfollow a user on Moltbook.',
    'validate': validate_follow_action,
    'handler': handle_follow_action
}
