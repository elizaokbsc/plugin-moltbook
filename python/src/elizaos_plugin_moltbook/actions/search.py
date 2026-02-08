"""
Search Action

Search for posts and comments on Moltbook using semantic search.

Python port of TypeScript search action
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def extract_search_query(text: str) -> Dict[str, Any]:
    """Extract search query and type from message text"""
    text_lower = text.lower()
    
    # Determine search type
    search_type = 'all'
    if 'posts' in text_lower and 'comments' not in text_lower:
        search_type = 'posts'
    elif 'comments' in text_lower and 'posts' not in text_lower:
        search_type = 'comments'
    
    # Extract query (remove search-related words)
    query = text
    for word in ['search', 'find', 'look for', 'moltbook', 'on moltbook']:
        query = query.replace(word, '').strip()
    
    # Remove quotes if present
    query = query.strip('"\'')
    
    return {
        'query': query,
        'search_type': search_type
    }


def format_search_results(results: List[Dict]) -> str:
    """Format search results for display"""
    if not results:
        return "No results found."
    
    lines = [f"Found {len(results)} result(s):", ""]
    
    for i, result in enumerate(results[:10], 1):
        result_type = result.get('type', 'unknown')
        title = result.get('title', '')
        content = result.get('content', '')[:100]
        author = result.get('author', {}).get('name', 'Unknown')
        score = result.get('upvotes', 0) - result.get('downvotes', 0)
        
        if result_type == 'post':
            lines.append(f"{i}. [POST] \"{title}\" by {author} ({score}↑)")
            lines.append(f"   {content}...")
        else:
            post_title = result.get('post', {}).get('title', 'Unknown post')
            lines.append(f"{i}. [COMMENT] on \"{post_title}\" by {author} ({score}↑)")
            lines.append(f"   {content}...")
        
        lines.append("")
    
    return "\n".join(lines)


async def validate_search_action(runtime: Any, message: Any, state: Optional[Any] = None) -> bool:
    """Validate if this is a search action"""
    text = getattr(message.content, 'text', '') or str(message.content)
    text_lower = text.lower()
    
    # Check for search intent
    has_search_intent = any(keyword in text_lower for keyword in [
        'search', 'find', 'look for', 'query'
    ])
    
    has_moltbook_mention = any(keyword in text_lower for keyword in [
        'moltbook', 'molty', 'posts', 'comments'
    ])
    
    return has_search_intent and has_moltbook_mention


async def handle_search_action(
    runtime: Any,
    message: Any,
    state: Optional[Any],
    options: Any,
    callback: Any
) -> Dict[str, Any]:
    """Handle search action"""
    
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
    
    # Extract search intent
    text = getattr(message.content, 'text', '') or str(message.content)
    intent = extract_search_query(text)
    
    query = intent['query']
    if not query or len(query) < 3:
        error_msg = 'Please provide a search query (at least 3 characters).'
        if callback:
            await callback({'text': error_msg})
        return {'success': False, 'error': error_msg}
    
    try:
        # Call API
        from ..lib.api import search
        results = await search(
            agent_id=str(runtime.agent_id),
            api_key=creds['apiKey'],
            query=query,
            search_type=intent['search_type'],
            limit=10
        )
        
        if results:
            result_list = results.get('results', [])
            result_text = format_search_results(result_list)
            
            if callback:
                await callback({'text': result_text})
            
            logger.info(f"Search completed: {len(result_list)} results for '{query}'")
            return {
                'success': True,
                'text': result_text,
                'data': {'query': query, 'results': result_list}
            }
        else:
            error_msg = f"Search failed for query: {query}"
            if callback:
                await callback({'text': error_msg, 'error': True})
            return {'success': False, 'error': error_msg}
            
    except Exception as e:
        error_msg = f"Error searching: {str(e)}"
        logger.error(error_msg)
        if callback:
            await callback({'text': error_msg, 'error': True})
        return {'success': False, 'error': error_msg}


# Action definition for plugin registration
SEARCH_ACTION = {
    'name': 'MOLTBOOK_SEARCH',
    'similes': ['SEARCH_MOLTBOOK', 'FIND_MOLTBOOK_POSTS', 'QUERY_MOLTBOOK'],
    'description': 'Search for posts and comments on Moltbook using semantic search.',
    'validate': validate_search_action,
    'handler': handle_search_action
}
