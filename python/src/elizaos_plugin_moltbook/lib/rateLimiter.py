"""
Rate Limiter for Moltbook API

TWO LEVELS OF RATE LIMITING:

1. GLOBAL (IP-level) - Shared across ALL agents in this process
2. PER-AGENT - Each agent has their own Moltbook account limits

Python port of TypeScript rateLimiter from plugin-moltbook/typescript/src/lib/rateLimiter.ts
"""

import time
from typing import Dict, List, Optional
from ..types import RateLimitState, RateLimitRequest, AgentMoltbookState
from ..constants import (
    RATE_LIMIT_REQUESTS_PER_MIN,
    RATE_LIMIT_POST_INTERVAL_SEC,
    RATE_LIMIT_COMMENTS_PER_HOUR,
    RATE_LIMIT_REQUEST_WINDOW_MS,
    RATE_LIMIT_COMMENT_WINDOW_MS,
    GLOBAL_REQUESTS_PER_MIN,
    GLOBAL_POSTS_PER_HOUR,
)

# =============================================================================
# GLOBAL RATE LIMITING (IP-level protection)
# =============================================================================

GLOBAL_REQUEST_WINDOW_MS = 60 * 1000  # 1 minute
GLOBAL_POST_WINDOW_MS = 60 * 60 * 1000  # 1 hour


class GlobalRateLimitState:
    """Global state shared across ALL agents"""
    def __init__(self):
        self.requests: List[RateLimitRequest] = []
        self.posts: List[RateLimitRequest] = []
        self.retry_after: Optional[int] = None


# Global singleton
_global_state = GlobalRateLimitState()


def _current_time_ms() -> int:
    """Get current time in milliseconds"""
    return int(time.time() * 1000)


def can_make_global_request() -> bool:
    """Check if we can make a request globally (IP-level)"""
    # Check global retry-after
    if _global_state.retry_after and _current_time_ms() < _global_state.retry_after:
        return False
    
    # Prune old requests
    cutoff = _current_time_ms() - GLOBAL_REQUEST_WINDOW_MS
    _global_state.requests = [r for r in _global_state.requests if r.timestamp > cutoff]
    
    return len(_global_state.requests) < GLOBAL_REQUESTS_PER_MIN


def can_post_globally() -> bool:
    """Check if we can post globally (IP-level)"""
    cutoff = _current_time_ms() - GLOBAL_POST_WINDOW_MS
    _global_state.posts = [p for p in _global_state.posts if p.timestamp > cutoff]
    
    return len(_global_state.posts) < GLOBAL_POSTS_PER_HOUR


def record_global_request() -> None:
    """Record a global request"""
    _global_state.requests.append(RateLimitRequest(timestamp=_current_time_ms()))


def record_global_post() -> None:
    """Record a global post"""
    _global_state.posts.append(RateLimitRequest(timestamp=_current_time_ms()))


def set_global_retry_after(retry_after_seconds: int) -> None:
    """Set global retry-after (affects ALL agents)"""
    _global_state.retry_after = _current_time_ms() + retry_after_seconds * 1000


def get_global_rate_limit_status() -> Dict:
    """Get global rate limit status"""
    request_cutoff = _current_time_ms() - GLOBAL_REQUEST_WINDOW_MS
    post_cutoff = _current_time_ms() - GLOBAL_POST_WINDOW_MS
    
    _global_state.requests = [r for r in _global_state.requests if r.timestamp > request_cutoff]
    _global_state.posts = [p for p in _global_state.posts if p.timestamp > post_cutoff]
    
    return {
        'can_request': can_make_global_request(),
        'can_post': can_post_globally(),
        'requests_used': len(_global_state.requests),
        'requests_max': GLOBAL_REQUESTS_PER_MIN,
        'posts_used': len(_global_state.posts),
        'posts_max': GLOBAL_POSTS_PER_HOUR,
        'retry_after': _global_state.retry_after,
    }


# =============================================================================
# PER-AGENT RATE LIMITING
# =============================================================================

# Per-agent state storage
_agent_states: Dict[str, AgentMoltbookState] = {}


def get_agent_state(agent_id: str) -> AgentMoltbookState:
    """Get or create state for an agent"""
    if agent_id not in _agent_states:
        _agent_states[agent_id] = AgentMoltbookState(
            rateLimits=RateLimitState()
        )
    return _agent_states[agent_id]


def _prune_old_entries(entries: List[RateLimitRequest], window_ms: int) -> List[RateLimitRequest]:
    """Clean up old entries from rate limit arrays"""
    cutoff = _current_time_ms() - window_ms
    return [e for e in entries if e.timestamp > cutoff]


def can_make_request(agent_id: str) -> bool:
    """Check if we can make a general API request
    
    Checks BOTH global (IP-level) and per-agent limits.
    """
    # FIRST: Check global (IP-level) limits
    if not can_make_global_request():
        return False
    
    # THEN: Check per-agent limits
    state = get_agent_state(agent_id)
    
    # Check agent-specific retry-after
    if state.rateLimits.retryAfter and _current_time_ms() < state.rateLimits.retryAfter:
        return False
    
    # Prune old requests
    state.rateLimits.requests = _prune_old_entries(
        state.rateLimits.requests,
        RATE_LIMIT_REQUEST_WINDOW_MS
    )
    
    return len(state.rateLimits.requests) < RATE_LIMIT_REQUESTS_PER_MIN


def record_request(agent_id: str) -> None:
    """Record a request was made
    
    Records in BOTH global and per-agent tracking.
    """
    # Record globally
    record_global_request()
    
    # Record per-agent
    state = get_agent_state(agent_id)
    state.rateLimits.requests.append(RateLimitRequest(timestamp=_current_time_ms()))


def set_retry_after(agent_id: str, retry_after_seconds: int) -> None:
    """Set retry-after from server response
    
    Sets for the specific agent, AND globally.
    """
    # Set for this agent
    state = get_agent_state(agent_id)
    state.rateLimits.retryAfter = _current_time_ms() + retry_after_seconds * 1000
    
    # ALSO set globally - if one agent gets 429, all should pause
    set_global_retry_after(retry_after_seconds)


def can_post(agent_id: str) -> bool:
    """Check if we can make a post
    
    Checks BOTH global and per-agent post limits.
    """
    # FIRST: Check if requests are allowed at all
    if not can_make_request(agent_id):
        return False
    
    # SECOND: Check global post limit (IP-level)
    if not can_post_globally():
        return False
    
    # THIRD: Check per-agent post limit
    state = get_agent_state(agent_id)
    
    # Get the most recent post
    if state.rateLimits.posts:
        last_post = state.rateLimits.posts[-1]
        time_since_last_post = _current_time_ms() - last_post.timestamp
        if time_since_last_post < RATE_LIMIT_POST_INTERVAL_SEC * 1000:
            return False
    
    return True


def record_post(agent_id: str) -> None:
    """Record a post was made
    
    Records in BOTH global and per-agent tracking.
    """
    # Record globally
    record_global_post()
    
    # Record per-agent
    state = get_agent_state(agent_id)
    state.rateLimits.posts.append(RateLimitRequest(timestamp=_current_time_ms()))
    record_request(agent_id)


def get_time_until_can_post(agent_id: str) -> int:
    """Get time until next post is allowed (in ms)"""
    state = get_agent_state(agent_id)
    
    if not state.rateLimits.posts:
        return 0
    
    last_post = state.rateLimits.posts[-1]
    elapsed = _current_time_ms() - last_post.timestamp
    required = RATE_LIMIT_POST_INTERVAL_SEC * 1000
    
    return max(0, required - elapsed)


def can_comment(agent_id: str) -> bool:
    """Check if we can make a comment"""
    if not can_make_request(agent_id):
        return False
    
    state = get_agent_state(agent_id)
    
    # Prune old comments
    state.rateLimits.comments = _prune_old_entries(
        state.rateLimits.comments,
        RATE_LIMIT_COMMENT_WINDOW_MS
    )
    
    return len(state.rateLimits.comments) < RATE_LIMIT_COMMENTS_PER_HOUR


def record_comment(agent_id: str) -> None:
    """Record a comment was made"""
    state = get_agent_state(agent_id)
    state.rateLimits.comments.append(RateLimitRequest(timestamp=_current_time_ms()))
    record_request(agent_id)


def get_remaining_comments(agent_id: str) -> int:
    """Get remaining comment quota"""
    state = get_agent_state(agent_id)
    
    # Prune old comments
    state.rateLimits.comments = _prune_old_entries(
        state.rateLimits.comments,
        RATE_LIMIT_COMMENT_WINDOW_MS
    )
    
    return RATE_LIMIT_COMMENTS_PER_HOUR - len(state.rateLimits.comments)


def get_rate_limit_status(agent_id: str) -> Dict:
    """Get rate limit status summary for an agent"""
    state = get_agent_state(agent_id)
    
    # Prune old entries
    state.rateLimits.requests = _prune_old_entries(
        state.rateLimits.requests,
        RATE_LIMIT_REQUEST_WINDOW_MS
    )
    state.rateLimits.comments = _prune_old_entries(
        state.rateLimits.comments,
        RATE_LIMIT_COMMENT_WINDOW_MS
    )
    
    return {
        'can_request': can_make_request(agent_id),
        'can_post': can_post(agent_id),
        'can_comment': can_comment(agent_id),
        'requests_remaining': RATE_LIMIT_REQUESTS_PER_MIN - len(state.rateLimits.requests),
        'comments_remaining': RATE_LIMIT_COMMENTS_PER_HOUR - len(state.rateLimits.comments),
        'time_until_can_post': get_time_until_can_post(agent_id),
        'retry_after': state.rateLimits.retryAfter,
    }


def clear_agent_state(agent_id: str) -> None:
    """Clear all state for an agent (useful for testing)"""
    if agent_id in _agent_states:
        del _agent_states[agent_id]


def clear_all_states() -> None:
    """Clear all agent states (useful for testing)"""
    _agent_states.clear()
    _global_state.requests.clear()
    _global_state.posts.clear()
    _global_state.retry_after = None
