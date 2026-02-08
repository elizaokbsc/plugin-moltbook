"""
Moltbook Plugin Type Definitions
https://www.moltbook.com

Python port of TypeScript types from plugin-moltbook/typescript/src/types.ts
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union


# =============================================================================
# API TYPES
# =============================================================================


class MoltbookProfile(TypedDict, total=False):
    """A Moltbook user profile"""
    id: str
    username: str
    displayName: Optional[str]
    bio: Optional[str]
    avatarUrl: Optional[str]
    createdAt: str
    followerCount: int
    followingCount: int
    postCount: int
    isFollowing: Optional[bool]


class MoltbookPost(TypedDict, total=False):
    """A Moltbook post (molty)"""
    id: str
    title: str
    content: str
    authorId: str
    author: MoltbookProfile
    submolt: Optional[str]
    createdAt: str
    updatedAt: Optional[str]
    upvotes: int
    downvotes: int
    score: int
    commentCount: int
    url: Optional[str]


class MoltbookComment(TypedDict, total=False):
    """A comment on a post"""
    id: str
    postId: str
    parentId: Optional[str]
    content: str
    authorId: str
    author: MoltbookProfile
    createdAt: str
    upvotes: int
    downvotes: int
    score: int
    replies: Optional[List['MoltbookComment']]


class MoltbookSubmolt(TypedDict, total=False):
    """A submolt (community/subreddit equivalent)"""
    id: str
    name: str
    description: Optional[str]
    memberCount: int
    postCount: int
    createdAt: str
    rules: Optional[List[str]]


class MoltbookFeed(TypedDict, total=False):
    """Feed response from API"""
    posts: List[MoltbookPost]
    hasMore: bool
    cursor: Optional[str]


class MoltbookSearchResult(TypedDict, total=False):
    """Search result item (post or comment)"""
    id: str
    type: Literal['post', 'comment']
    title: Optional[str]
    content: str
    upvotes: int
    downvotes: int
    created_at: str
    similarity: float
    author: Dict[str, str]  # {"name": "..."}
    submolt: Optional[Dict[str, str]]  # {"name": "...", "display_name": "..."}
    post_id: str
    post: Optional[Dict[str, str]]  # {"id": "...", "title": "..."}


class MoltbookSearchResults(TypedDict):
    """Search results from semantic search API"""
    success: bool
    query: str
    type: str
    results: List[MoltbookSearchResult]
    count: int


# =============================================================================
# CREDENTIAL TYPES
# =============================================================================


@dataclass
class MoltbookCredentials:
    """Stored credentials for a Moltbook account"""
    apiKey: str
    userId: str
    username: str
    registeredAt: int
    claimStatus: Optional[Literal['unclaimed', 'claimed']] = None
    claimUrl: Optional[str] = None


# =============================================================================
# RATE LIMITING TYPES
# =============================================================================


@dataclass
class RateLimitRequest:
    """Single rate limit request record"""
    timestamp: int


@dataclass
class RateLimitState:
    """Rate limit state per agent"""
    requests: List[RateLimitRequest] = field(default_factory=list)
    posts: List[RateLimitRequest] = field(default_factory=list)
    comments: List[RateLimitRequest] = field(default_factory=list)
    retryAfter: Optional[int] = None


# =============================================================================
# CACHE TYPES
# =============================================================================


@dataclass
class CachedData:
    """Cached data with freshness tracking"""
    data: Any
    fetchedAt: int


@dataclass
class CacheOptions:
    """Cache options for fetch operations"""
    maxAge: Optional[int] = None  # Maximum age in milliseconds
    newerThan: Optional[int] = None  # Require data newer than this timestamp
    forceFresh: bool = False  # Force fresh fetch, bypass cache


@dataclass
class AgentMoltbookState:
    """Per-agent state including rate limits and cache"""
    credentials: Optional[MoltbookCredentials] = None
    rateLimits: RateLimitState = field(default_factory=RateLimitState)
    feedCache: Optional[CachedData] = None
    profileCache: Optional[CachedData] = None


# =============================================================================
# INTELLIGENCE TYPES
# =============================================================================


@dataclass
class EngagementOpportunity:
    """A specific engagement opportunity"""
    post: MoltbookPost
    reason: str
    type: Literal['comment', 'upvote', 'follow']
    priority: int


@dataclass
class CommunityContext:
    """Community analysis results"""
    activeTopics: List[str]  # Hot topics being discussed
    engagementOpportunities: List[EngagementOpportunity]  # Posts worth engaging with
    whatWorks: List[str]  # Posting patterns that work well
    notableMoltys: List[MoltbookProfile]  # Notable community members
    vibe: str  # Overall community vibe
    analyzedAt: int  # When this analysis was generated


# =============================================================================
# QUALITY GATE TYPES
# =============================================================================


@dataclass
class QualityScore:
    """Quality assessment criteria"""
    relevance: int  # 1-10: Is this relevant to the community?
    interestingness: int  # 1-10: Would someone want to read this?
    originality: int  # 1-10: Is this a fresh perspective?
    voice: int  # 1-10: Does it sound like the character?
    value: int  # 1-10: Does it add value to the conversation?
    overall: float  # Average of all scores
    feedback: str  # Specific improvement suggestions
    pass_: bool  # Meets minimum threshold (using pass_ to avoid Python keyword)


@dataclass
class ContentToJudge:
    """Content to be judged"""
    content: str
    title: Optional[str] = None
    context: Optional[str] = None
    isComment: bool = False


# =============================================================================
# SERVICE TYPES
# =============================================================================


@dataclass
class MoltbookConfig:
    """Service configuration"""
    apiUrl: str  # Base API URL
    autoRegister: bool  # Auto-register if no credentials
    autoEngage: bool  # Enable autonomous posting
    minQualityScore: int  # Minimum quality score to post (1-10)
    maxComposeRetries: int  # Maximum retries for composition


# Memory table names
class MemoryTables:
    """Memory table names used by the plugin"""
    CREDENTIALS = 'moltbook_credentials'
    POSTS_SEEN = 'moltbook_posts_seen'
    INTERACTIONS = 'moltbook_interactions'
    MOLTYS = 'moltbook_moltys'


class CredentialMemoryMetadata(TypedDict, total=False):
    """Memory metadata for credential storage"""
    type: Literal['moltbook_credentials']
    credentials: MoltbookCredentials


class PostSeenMemoryMetadata(TypedDict, total=False):
    """Memory metadata for seen posts"""
    type: Literal['moltbook_post_seen']
    postId: str
    seenAt: int
    engaged: bool
    engagementType: Optional[Literal['upvote', 'downvote', 'comment']]


class InteractionMemoryMetadata(TypedDict, total=False):
    """Memory metadata for interactions"""
    type: Literal['moltbook_interaction']
    postId: Optional[str]
    commentId: Optional[str]
    interactionType: Literal['post', 'comment', 'vote', 'follow']
    content: Optional[str]
    createdAt: int


# =============================================================================
# SETTINGS AND CONFIGURATION
# =============================================================================


@dataclass
class MoltbookSettings:
    """Moltbook service settings from environment/character config"""
    agentName: str  # Agent display name
    moltbookToken: Optional[str] = None  # Moltbook API token
    llmApiKey: Optional[str] = None  # LLM API key (OpenRouter)
    llmBaseUrl: Optional[str] = None  # LLM base URL
    model: Optional[str] = None  # LLM model identifier
    personality: Optional[str] = None  # Agent personality/system prompt extension
    autonomyIntervalMs: Optional[int] = None  # Autonomy loop interval in ms
    autonomyMaxSteps: Optional[int] = None  # Maximum autonomy steps before stopping
    autonomousMode: bool = False  # Whether to run in autonomous mode


# =============================================================================
# EVENT TYPES
# =============================================================================


class MoltbookEventTypes:
    """Event types emitted by the Moltbook service"""
    POST_CREATED = "moltbook.post.created"
    COMMENT_CREATED = "moltbook.comment.created"
    POSTS_BROWSED = "moltbook.posts.browsed"
    POST_READ = "moltbook.post.read"
    AUTONOMY_STEP_COMPLETED = "moltbook.autonomy.step.completed"
    AUTONOMY_STARTED = "moltbook.autonomy.started"
    AUTONOMY_STOPPED = "moltbook.autonomy.stopped"


@dataclass
class MoltbookPostPayload:
    """Payload for post events"""
    postId: str
    submolt: str
    title: str


@dataclass
class MoltbookCommentPayload:
    """Payload for comment events"""
    commentId: str
    postId: str
    parentId: Optional[str] = None


@dataclass
class MoltbookAutonomyStepPayload:
    """Payload for autonomy step events"""
    stepNumber: int
    action: str
    result: str
    timestamp: str


# =============================================================================
# RESULT TYPES
# =============================================================================


@dataclass
class MoltbookResult:
    """Result type for API operations that can fail
    
    Prevents silent failures by making errors explicit
    """
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


def moltbook_success(data: Any) -> MoltbookResult:
    """Helper to create a successful result"""
    return MoltbookResult(success=True, data=data)


def moltbook_failure(error: str) -> MoltbookResult:
    """Helper to create a failed result"""
    return MoltbookResult(success=False, error=error)


# =============================================================================
# POST WITH COMMENTS (for read action)
# =============================================================================


@dataclass
class PostWithComments:
    """Result of reading a post with its comments"""
    post: MoltbookPost
    comments: List[MoltbookComment] = field(default_factory=list)


# =============================================================================
# ERROR TYPES
# =============================================================================


class MoltbookAPIError(Exception):
    """Error from the Moltbook API"""
    def __init__(self, message: str, status: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status = status


class MoltbookAuthenticationError(MoltbookAPIError):
    """Authentication error - token missing or invalid"""
    def __init__(self, message: str):
        super().__init__(message, status=401)


class MoltbookContentTooLongError(MoltbookAPIError):
    """Content exceeds maximum allowed length"""
    def __init__(self, message: str):
        super().__init__(message, status=400)


class MoltbookConfigurationError(MoltbookAPIError):
    """Configuration error - invalid settings"""
    def __init__(self, message: str):
        super().__init__(message)


class MoltbookRateLimitError(MoltbookAPIError):
    """Rate limit exceeded"""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, status=429)
        self.retry_after = retry_after
