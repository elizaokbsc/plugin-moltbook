"""
Moltbook Plugin for elizaOS (Python)

Enables AI agents to participate in the Moltbook social network
as genuine community members.
"""

# Core plugin
from .plugin import moltbook_plugin, default

# Service
from .services.moltbook import MoltbookService

# Actions
from .actions import (
    moltbook_browse_action,
    moltbook_comment_action,
    moltbook_post_action,
    moltbook_read_action,
    moltbook_submolts_action,
    FOLLOW_ACTION,
    SEARCH_ACTION,
    VOTE_ACTION,
)

# Providers
from .providers import (
    moltbook_state_provider,
    MOLTBOOK_CONTEXT_PROVIDER,
)

# Evaluators
from .evaluators import REFLECTION_EVALUATOR

# Tasks
from .tasks import CYCLE_TASK

# Types
from .types import (
    MoltbookPost,
    MoltbookComment,
    MoltbookProfile,
    MoltbookFeed,
    MoltbookSubmolt,
    MoltbookCredentials,
    MoltbookResult,
    moltbook_success,
    moltbook_failure,
)

# Constants
from .constants import (
    PLUGIN_NAME,
    PLUGIN_DESCRIPTION,
    MOLTBOOK_API_URL,
    ENDPOINTS,
)

# Environment utilities
from .environment import (
    get_moltbook_settings,
    validate_moltbook_settings,
)

# Learning utilities
from .lib.learning import (
    store_observation,
    store_cultural_learning,
    remember_notable_user,
    get_cultural_learnings,
    get_notable_users,
    get_recent_observations,
    get_learnings_summary,
    format_cultural_learnings,
    format_notable_users,
)

# Mentions utilities
from .lib.mentions import (
    poll_for_mentions,
    process_mentions,
    record_my_post,
    get_my_posts,
    comment_to_memory,
)

__version__ = "2.0.0-python"

__all__ = [
    # Core
    'moltbook_plugin',
    'default',
    'MoltbookService',
    
    # Actions
    'moltbook_browse_action',
    'moltbook_comment_action',
    'moltbook_post_action',
    'moltbook_read_action',
    'moltbook_submolts_action',
    'FOLLOW_ACTION',
    'SEARCH_ACTION',
    'VOTE_ACTION',
    
    # Providers
    'moltbook_state_provider',
    'MOLTBOOK_CONTEXT_PROVIDER',
    
    # Evaluators
    'REFLECTION_EVALUATOR',
    
    # Tasks
    'CYCLE_TASK',
    
    # Types
    'MoltbookPost',
    'MoltbookComment',
    'MoltbookProfile',
    'MoltbookFeed',
    'MoltbookSubmolt',
    'MoltbookCredentials',
    'MoltbookResult',
    'moltbook_success',
    'moltbook_failure',
    
    # Constants
    'PLUGIN_NAME',
    'PLUGIN_DESCRIPTION',
    'MOLTBOOK_API_URL',
    'ENDPOINTS',
    
    # Utilities
    'get_moltbook_settings',
    'validate_moltbook_settings',
    'store_observation',
    'store_cultural_learning',
    'remember_notable_user',
    'get_cultural_learnings',
    'get_notable_users',
    'get_recent_observations',
    'get_learnings_summary',
    'format_cultural_learnings',
    'format_notable_users',
    'poll_for_mentions',
    'process_mentions',
    'record_my_post',
    'get_my_posts',
    'comment_to_memory',
]
