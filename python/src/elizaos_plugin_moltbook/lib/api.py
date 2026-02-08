"""
Moltbook API Client

HTTP client with per-agent rate limiting, retry logic, and error handling.

Python port of TypeScript api from plugin-moltbook/typescript/src/lib/api.ts
"""

import asyncio
import httpx
import logging
from typing import Any, Dict, List, Literal, Optional
from ..types import (
    MoltbookPost,
    MoltbookComment,
    MoltbookProfile,
    MoltbookFeed,
    MoltbookSearchResults,
    MoltbookSubmolt,
    MoltbookCredentials,
    MoltbookAPIError,
    MoltbookAuthenticationError,
    MoltbookRateLimitError,
)
from ..constants import (
    MOLTBOOK_API_URL,
    ENDPOINTS,
    HTTP_TIMEOUT_MS,
    HTTP_MAX_RETRIES,
    HTTP_RETRY_BASE_DELAY_MS,
)
from . import rateLimiter

logger = logging.getLogger(__name__)


# =============================================================================
# TYPES
# =============================================================================

class ApiResponse:
    """API response wrapper"""
    def __init__(self, success: bool, data: Any = None, error: Optional[str] = None, status: Optional[int] = None):
        self.success = success
        self.data = data
        self.error = error
        self.status = status


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

async def _request(
    agent_id: str,
    endpoint: str,
    api_key: Optional[str],
    method: Literal['GET', 'POST', 'PUT', 'DELETE', 'PATCH'] = 'GET',
    body: Optional[Dict] = None,
    headers: Optional[Dict[str, str]] = None,
    skip_rate_limit: bool = False,
) -> ApiResponse:
    """Make an HTTP request with retries and rate limiting"""
    
    # Check rate limits (unless skipped for auth endpoints)
    if not skip_rate_limit and not rateLimiter.can_make_request(agent_id):
        logger.warning(f"Rate limited locally: {endpoint}")
        return ApiResponse(
            success=False,
            error='Rate limited - too many requests',
            status=429
        )
    
    url = f"{MOLTBOOK_API_URL}{endpoint}"
    request_headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'elizaOS-moltbook-plugin/2.0-python',
        **(headers or {})
    }
    
    if api_key:
        request_headers['Authorization'] = f'Bearer {api_key}'
    
    logger.debug(f"Making request: {method} {url}")
    
    last_error = None
    timeout_seconds = HTTP_TIMEOUT_MS / 1000
    
    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        for attempt in range(HTTP_MAX_RETRIES):
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    json=body if body else None
                )
                
                # Record the request for rate limiting
                if not skip_rate_limit:
                    rateLimiter.record_request(agent_id)
                
                # Handle rate limit response
                if response.status_code == 429:
                    retry_after = response.headers.get('retry-after')
                    logger.warning(f"Rate limited by server: {url}")
                    if retry_after:
                        rateLimiter.set_retry_after(agent_id, int(retry_after))
                    return ApiResponse(
                        success=False,
                        error='Rate limited by server',
                        status=429
                    )
                
                # Handle other error statuses
                if not response.is_success:
                    error_body = response.text
                    logger.error(f"API error: {response.status_code} {error_body}")
                    
                    # Retry on 5xx errors
                    if 500 <= response.status_code < 600:
                        if attempt < HTTP_MAX_RETRIES - 1:
                            delay_ms = HTTP_RETRY_BASE_DELAY_MS * (2 ** attempt)
                            await asyncio.sleep(delay_ms / 1000)
                            continue
                    
                    return ApiResponse(
                        success=False,
                        error=f"HTTP {response.status_code}: {error_body}",
                        status=response.status_code
                    )
                
                # Parse successful response
                try:
                    data = response.json() if response.text else None
                    logger.debug(f"Success: {method} {url}")
                    return ApiResponse(success=True, data=data, status=response.status_code)
                except Exception as e:
                    logger.error(f"Failed to parse response: {e}")
                    return ApiResponse(
                        success=False,
                        error=f"Failed to parse response: {str(e)}",
                        status=response.status_code
                    )
                    
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Request timeout (attempt {attempt + 1}/{HTTP_MAX_RETRIES}): {url}")
                if attempt < HTTP_MAX_RETRIES - 1:
                    delay_ms = HTTP_RETRY_BASE_DELAY_MS * (2 ** attempt)
                    await asyncio.sleep(delay_ms / 1000)
                continue
                
            except Exception as e:
                last_error = e
                logger.error(f"Request failed: {e}")
                if attempt < HTTP_MAX_RETRIES - 1:
                    delay_ms = HTTP_RETRY_BASE_DELAY_MS * (2 ** attempt)
                    await asyncio.sleep(delay_ms / 1000)
                continue
    
    # All retries exhausted
    return ApiResponse(
        success=False,
        error=f"Request failed after {HTTP_MAX_RETRIES} attempts: {str(last_error)}"
    )


# =============================================================================
# AUTHENTICATION
# =============================================================================

async def register_agent(
    agent_id: str,
    name: str,
    description: str = ""
) -> Optional[MoltbookCredentials]:
    """Register a new agent account"""
    logger.info(f"Registering new agent: {name}")
    
    response = await _request(
        agent_id=agent_id,
        endpoint=ENDPOINTS.REGISTER,
        api_key=None,
        method='POST',
        body={'name': name, 'description': description},
        skip_rate_limit=True  # Don't rate limit registration
    )
    
    if not response.success:
        logger.error(f"Registration failed: {response.error}")
        return None
    
    data = response.data
    return MoltbookCredentials(
        apiKey=data.get('api_key', ''),
        userId=data.get('id', ''),
        username=data.get('name', name),
        registeredAt=int(asyncio.get_event_loop().time() * 1000),
        claimStatus=data.get('claim_status'),
        claimUrl=data.get('claim_url')
    )


async def get_profile(agent_id: str, api_key: str, username: Optional[str] = None) -> Optional[MoltbookProfile]:
    """Get agent profile (self or other)"""
    endpoint = ENDPOINTS.AGENT_PROFILE(username) if username else ENDPOINTS.ME
    
    response = await _request(
        agent_id=agent_id,
        endpoint=endpoint,
        api_key=api_key,
        method='GET'
    )
    
    return response.data if response.success else None


# =============================================================================
# POSTS
# =============================================================================

async def get_posts(
    agent_id: str,
    api_key: str,
    submolt: Optional[str] = None,
    sort: str = 'hot',
    limit: int = 10
) -> Optional[MoltbookFeed]:
    """Get posts feed"""
    endpoint = ENDPOINTS.SUBMOLT_FEED(submolt) if submolt else ENDPOINTS.FEED
    params = f"?sort={sort}&limit={limit}"
    
    response = await _request(
        agent_id=agent_id,
        endpoint=f"{endpoint}{params}",
        api_key=api_key,
        method='GET'
    )
    
    if not response.success:
        return None
    
    data = response.data
    return {
        'posts': data.get('posts', []),
        'hasMore': data.get('has_more', False),
        'cursor': data.get('cursor')
    }


async def get_post(agent_id: str, api_key: str, post_id: str) -> Optional[MoltbookPost]:
    """Get a single post"""
    response = await _request(
        agent_id=agent_id,
        endpoint=ENDPOINTS.POST_BY_ID(post_id),
        api_key=api_key,
        method='GET'
    )
    
    return response.data if response.success else None


async def create_post(
    agent_id: str,
    api_key: str,
    title: str,
    content: str,
    submolt: Optional[str] = None
) -> Optional[MoltbookPost]:
    """Create a new post"""
    
    # Check rate limits
    if not rateLimiter.can_post(agent_id):
        logger.warning("Cannot post - rate limited")
        return None
    
    body = {'title': title, 'content': content}
    if submolt:
        body['submolt'] = submolt
    
    response = await _request(
        agent_id=agent_id,
        endpoint=ENDPOINTS.POSTS,
        api_key=api_key,
        method='POST',
        body=body
    )
    
    if response.success:
        rateLimiter.record_post(agent_id)
        return response.data
    
    return None


# =============================================================================
# COMMENTS
# =============================================================================

async def get_comments(agent_id: str, api_key: str, post_id: str) -> List[MoltbookComment]:
    """Get comments for a post"""
    response = await _request(
        agent_id=agent_id,
        endpoint=ENDPOINTS.COMMENTS(post_id),
        api_key=api_key,
        method='GET'
    )
    
    return response.data if response.success else []


async def create_comment(
    agent_id: str,
    api_key: str,
    post_id: str,
    content: str,
    parent_id: Optional[str] = None
) -> Optional[MoltbookComment]:
    """Create a comment or reply"""
    
    # Check rate limits
    if not rateLimiter.can_comment(agent_id):
        logger.warning("Cannot comment - rate limited")
        return None
    
    body = {'content': content}
    if parent_id:
        body['parent_id'] = parent_id
    
    response = await _request(
        agent_id=agent_id,
        endpoint=ENDPOINTS.COMMENTS(post_id),
        api_key=api_key,
        method='POST',
        body=body
    )
    
    if response.success:
        rateLimiter.record_comment(agent_id)
        return response.data
    
    return None


# =============================================================================
# VOTING
# =============================================================================

async def vote_post(
    agent_id: str,
    api_key: str,
    post_id: str,
    vote: Literal['up', 'down']
) -> bool:
    """Vote on a post"""
    endpoint = ENDPOINTS.UPVOTE(post_id) if vote == 'up' else ENDPOINTS.DOWNVOTE(post_id)
    
    response = await _request(
        agent_id=agent_id,
        endpoint=endpoint,
        api_key=api_key,
        method='POST'
    )
    
    return response.success


async def vote_comment(
    agent_id: str,
    api_key: str,
    comment_id: str,
    vote: Literal['up', 'down']
) -> bool:
    """Vote on a comment"""
    endpoint = ENDPOINTS.COMMENT_UPVOTE(comment_id) if vote == 'up' else ENDPOINTS.COMMENT_DOWNVOTE(comment_id)
    
    response = await _request(
        agent_id=agent_id,
        endpoint=endpoint,
        api_key=api_key,
        method='POST'
    )
    
    return response.success


# =============================================================================
# FOLLOWS
# =============================================================================

async def follow_agent(
    agent_id: str,
    api_key: str,
    target_name: str,
    unfollow: bool = False
) -> bool:
    """Follow or unfollow an agent"""
    method = 'DELETE' if unfollow else 'POST'
    
    response = await _request(
        agent_id=agent_id,
        endpoint=ENDPOINTS.AGENT_FOLLOW(target_name),
        api_key=api_key,
        method=method
    )
    
    return response.success


# =============================================================================
# SUBMOLTS
# =============================================================================

async def get_submolts(agent_id: str, api_key: str, sort: str = 'popular') -> List[MoltbookSubmolt]:
    """Get all submolts"""
    response = await _request(
        agent_id=agent_id,
        endpoint=f"{ENDPOINTS.SUBMOLTS}?sort={sort}",
        api_key=api_key,
        method='GET'
    )
    
    return response.data if response.success else []


async def get_submolt(agent_id: str, api_key: str, name: str) -> Optional[MoltbookSubmolt]:
    """Get a specific submolt"""
    response = await _request(
        agent_id=agent_id,
        endpoint=ENDPOINTS.SUBMOLT_BY_NAME(name),
        api_key=api_key,
        method='GET'
    )
    
    return response.data if response.success else None


async def subscribe_submolt(
    agent_id: str,
    api_key: str,
    name: str,
    unsubscribe: bool = False
) -> bool:
    """Subscribe or unsubscribe from a submolt"""
    method = 'DELETE' if unsubscribe else 'POST'
    
    response = await _request(
        agent_id=agent_id,
        endpoint=ENDPOINTS.SUBMOLT_SUBSCRIBE(name),
        api_key=api_key,
        method=method
    )
    
    return response.success


# =============================================================================
# SEARCH
# =============================================================================

async def search(
    agent_id: str,
    api_key: str,
    query: str,
    search_type: Literal['posts', 'comments', 'all'] = 'all',
    limit: int = 10
) -> Optional[MoltbookSearchResults]:
    """Search posts and comments"""
    params = f"?q={query}&type={search_type}&limit={limit}"
    
    response = await _request(
        agent_id=agent_id,
        endpoint=f"{ENDPOINTS.SEARCH}{params}",
        api_key=api_key,
        method='GET'
    )
    
    return response.data if response.success else None
