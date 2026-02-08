"""
Moltbook Plugin Constants

Python port of TypeScript constants from plugin-moltbook/typescript/src/constants.ts

WHY CENTRALIZE CONSTANTS?

1. **Single Source of Truth**: All magic numbers in one place.
2. **Documentation**: Constants have comments explaining WHY they exist.
3. **Type Safety**: Centralized constants prevent typos.
4. **Easy Configuration**: All tunables are visible and adjustable.
"""

from typing import Callable, Dict

# =============================================================================
# API CONFIGURATION
# =============================================================================

# Base URL for the Moltbook API
# IMPORTANT: Must use www.moltbook.com!
# WHY? Without "www", the server redirects and strips Authorization header
MOLTBOOK_API_URL = 'https://www.moltbook.com/api/v1'


# API endpoints - based on https://www.moltbook.com/skill.md
class ENDPOINTS:
    """API endpoints (relative to MOLTBOOK_API_URL)"""
    
    # Authentication / Agent Management
    REGISTER = '/agents/register'
    ME = '/agents/me'
    STATUS = '/agents/status'
    
    @staticmethod
    def AGENT_PROFILE(name: str) -> str:
        from urllib.parse import quote
        return f'/agents/profile?name={quote(name)}'
    
    @staticmethod
    def AGENT_FOLLOW(name: str) -> str:
        from urllib.parse import quote
        return f'/agents/{quote(name)}/follow'
    
    # Posts
    FEED = '/feed'
    POSTS = '/posts'
    
    @staticmethod
    def POST_BY_ID(id: str) -> str:
        return f'/posts/{id}'
    
    # Comments
    @staticmethod
    def COMMENTS(post_id: str) -> str:
        return f'/posts/{post_id}/comments'
    
    # Voting
    @staticmethod
    def UPVOTE(post_id: str) -> str:
        return f'/posts/{post_id}/upvote'
    
    @staticmethod
    def DOWNVOTE(post_id: str) -> str:
        return f'/posts/{post_id}/downvote'
    
    @staticmethod
    def COMMENT_UPVOTE(comment_id: str) -> str:
        return f'/comments/{comment_id}/upvote'
    
    @staticmethod
    def COMMENT_DOWNVOTE(comment_id: str) -> str:
        return f'/comments/{comment_id}/downvote'
    
    # Submolts (communities)
    SUBMOLTS = '/submolts'
    
    @staticmethod
    def SUBMOLT_BY_NAME(name: str) -> str:
        return f'/submolts/{name}'
    
    @staticmethod
    def SUBMOLT_FEED(name: str) -> str:
        return f'/submolts/{name}/feed'
    
    @staticmethod
    def SUBMOLT_SUBSCRIBE(name: str) -> str:
        return f'/submolts/{name}/subscribe'
    
    # Search
    SEARCH = '/search'


# =============================================================================
# RATE LIMITS (per Moltbook API docs)
# =============================================================================

# Global limits (IP-level, shared across all agents)
GLOBAL_REQUESTS_PER_MIN = 200  # Conservative for shared IP
GLOBAL_POSTS_PER_HOUR = 20  # Prevents flooding from one IP

# Per-agent limits (Account-level)
RATE_LIMIT_REQUESTS_PER_MIN = 100  # General API requests
RATE_LIMIT_POST_INTERVAL_SEC = 30 * 60  # 30 minutes = 1800 seconds
RATE_LIMIT_COMMENTS_PER_HOUR = 50  # Max comments per hour

# Rate limit windows
RATE_LIMIT_REQUEST_WINDOW_MS = 60 * 1000  # 1 minute
RATE_LIMIT_COMMENT_WINDOW_MS = 60 * 60 * 1000  # 1 hour


# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

# Cache TTLs (Time To Live)
CACHE_TTL_FEED_MS = 5 * 60 * 1000  # 5 minutes - posts change frequently
CACHE_TTL_PROFILE_MS = 15 * 60 * 1000  # 15 minutes - profiles change rarely
CACHE_TTL_ANALYSIS_MS = 30 * 60 * 1000  # 30 minutes - community patterns evolve slowly


# =============================================================================
# QUALITY THRESHOLDS
# =============================================================================

# Minimum score (1-10) for autonomous posting
# WHY 7? High enough to filter mediocre content
MIN_QUALITY_SCORE_AUTONOMOUS = 7

# Minimum score for user-requested posting
# WHY 5? Trust human judgment more
MIN_QUALITY_SCORE_USER = 5

# Maximum composition retries before giving up
# WHY 3? Diminishing returns after a few attempts
MAX_COMPOSE_RETRIES = 3


# =============================================================================
# TASK CONFIGURATION
# =============================================================================

# Task name for the periodic cycle
MOLTBOOK_CYCLE_TASK = 'MOLTBOOK_CYCLE'

# Default cycle interval (15 minutes)
# WHY 15 MINUTES? Balance between staying current and not wasting resources
CYCLE_INTERVAL_MS = 15 * 60 * 1000

# Minimum time between autonomous posts (1 hour)
# WHY 1 HOUR? Feels more natural than posting every 30 minutes
MIN_AUTONOMOUS_POST_INTERVAL_MS = 60 * 60 * 1000


# =============================================================================
# MEMORY KEYS
# =============================================================================

# Key prefixes for credential and analysis storage
CRED_MEMORY_KEY = 'moltbook_creds'
COMMUNITY_ANALYSIS_KEY = 'moltbook_community_analysis'


# =============================================================================
# HTTP CONFIGURATION
# =============================================================================

# Request timeout in milliseconds
# WHY 30 SECONDS? Long enough for slow responses, short enough to fail fast
HTTP_TIMEOUT_MS = 30 * 1000

# Maximum retries for failed requests
# WHY 3? Handles transient failures without excessive hammering
HTTP_MAX_RETRIES = 3

# Base delay for exponential backoff (ms)
# Retry delays: 1s, 2s, 4s (exponential backoff)
HTTP_RETRY_BASE_DELAY_MS = 1000


# =============================================================================
# CONTENT LIMITS (per Moltbook API)
# =============================================================================

# Maximum content lengths
MAX_TITLE_LENGTH = 300
MAX_POST_LENGTH = 40000  # 40KB is generous for text
MAX_COMMENT_LENGTH = 10000


# =============================================================================
# PLUGIN METADATA
# =============================================================================

# Plugin name - used for service registration and logging
PLUGIN_NAME = 'moltbook'

# Plugin description
PLUGIN_DESCRIPTION = 'Moltbook social integration - community participation for AI agents'


# =============================================================================
# SERVICE AND AUTONOMY CONFIGURATION
# =============================================================================

# Service name for registration
MOLTBOOK_SERVICE_NAME = "moltbook"

# External service URLs
class URLS:
    """External service URLs"""
    MOLTBOOK = "https://www.moltbook.com/api/v1"
    OPENROUTER = "https://openrouter.ai/api/v1"


# Default autonomy settings
class AUTONOMY_DEFAULTS:
    """Default autonomy configuration"""
    MIN_INTERVAL_MS = 30000  # 30 seconds
    MAX_INTERVAL_MS = 90000  # 90 seconds
    MAX_TOOL_CALLS = 5  # Maximum tool calls per cycle
    DEFAULT_MODEL = "deepseek/deepseek-chat-v3-0324"  # Default LLM model


# Content limits (for API compatibility)
class CONTENT_LIMITS:
    """Content limits for API compatibility"""
    DEFAULT_BROWSE_LIMIT = 10  # Default number of posts to browse
    MAX_CONTENT_LENGTH = 10000  # Maximum post content length
    MAX_TITLE_LENGTH = 300  # Maximum title length
    MAX_COMMENT_LENGTH = 5000  # Maximum comment length


# Default submolt (subreddit equivalent)
DEFAULT_SUBMOLT = "iq"


# =============================================================================
# MEMORY TABLE NAMES
# =============================================================================

class MEMORY_TABLES:
    """Memory table names used by the plugin"""
    CREDENTIALS = 'moltbook_credentials'
    POSTS_SEEN = 'moltbook_posts_seen'
    INTERACTIONS = 'moltbook_interactions'
    MOLTYS = 'moltbook_moltys'
    OBSERVATIONS = 'moltbook_observations'  # Learning observations
    CULTURAL_LEARNINGS = 'moltbook_cultural_learnings'  # Cultural patterns
    NOTABLE_USERS = 'moltbook_notable_users'  # Notable community members
    MY_POSTS = 'moltbook_my_posts'  # Posts created by this agent
