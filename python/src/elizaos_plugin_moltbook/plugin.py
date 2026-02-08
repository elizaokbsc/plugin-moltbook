"""
Moltbook Plugin Definition

Main plugin export that registers the Moltbook service,
actions, providers, evaluators, and tasks with elizaOS.

Python port of TypeScript plugin
"""

import logging
from typing import Any, Dict, List, Optional

from .constants import PLUGIN_NAME, PLUGIN_DESCRIPTION
from .banner import print_banner, format_setting_for_display
from .environment import get_moltbook_settings, validate_moltbook_settings

# Import all components
from .services.moltbook import MoltbookService
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
from .providers import (
    moltbook_state_provider,
    MOLTBOOK_CONTEXT_PROVIDER,
)
from .evaluators import REFLECTION_EVALUATOR
from .tasks import CYCLE_TASK

logger = logging.getLogger(__name__)


async def init_plugin(config: Dict[str, Any], runtime: Any) -> None:
    """
    Plugin initialization - runs once at startup
    
    Args:
        config: Plugin configuration
        runtime: AgentRuntime instance
    """
    try:
        # Get and validate settings
        settings = get_moltbook_settings(runtime)
        is_valid, error = validate_moltbook_settings(settings)
        
        if not is_valid:
            raise ValueError(f"Invalid Moltbook configuration: {error}")
        
        # Format settings for display
        display_settings = [
            format_setting_for_display(
                'MOLTBOOK_API_KEY',
                runtime.get_setting('MOLTBOOK_API_KEY') if hasattr(runtime, 'get_setting') else None,
                sensitive=True
            ),
            format_setting_for_display(
                'MOLTBOOK_AUTO_REGISTER',
                runtime.get_setting('MOLTBOOK_AUTO_REGISTER', 'true') if hasattr(runtime, 'get_setting') else 'true'
            ),
            format_setting_for_display(
                'MOLTBOOK_AUTO_ENGAGE',
                runtime.get_setting('MOLTBOOK_AUTO_ENGAGE', 'false') if hasattr(runtime, 'get_setting') else 'false'
            ),
            format_setting_for_display(
                'MOLTBOOK_MIN_QUALITY_SCORE',
                runtime.get_setting('MOLTBOOK_MIN_QUALITY_SCORE', '7') if hasattr(runtime, 'get_setting') else '7'
            ),
        ]
        
        # Print banner
        print_banner(runtime=runtime, settings=display_settings)
        
        logger.info(f"Moltbook plugin initialized: {PLUGIN_NAME}")
        
    except Exception as e:
        logger.error(f"Error initializing Moltbook plugin: {e}")
        raise


# Plugin definition
moltbook_plugin = {
    'name': PLUGIN_NAME,
    'description': PLUGIN_DESCRIPTION,
    'version': '2.0.0-python',
    
    # Configuration with defaults
    'config': {
        'MOLTBOOK_API_KEY': None,
        'MOLTBOOK_AUTO_REGISTER': 'true',
        'MOLTBOOK_AUTO_ENGAGE': 'false',
        'MOLTBOOK_MIN_QUALITY_SCORE': '7',
    },
    
    # Initialization function
    'init': init_plugin,
    
    # Services
    'services': [MoltbookService],
    
    # Actions
    'actions': [
        moltbook_post_action,
        moltbook_comment_action,
        moltbook_browse_action,
        moltbook_read_action,
        moltbook_submolts_action,
        FOLLOW_ACTION,
        SEARCH_ACTION,
        VOTE_ACTION,
    ],
    
    # Providers
    'providers': [
        moltbook_state_provider,
        MOLTBOOK_CONTEXT_PROVIDER,
    ],
    
    # Evaluators
    'evaluators': [
        REFLECTION_EVALUATOR,
    ],
    
    # Tasks
    'tasks': [
        CYCLE_TASK,
    ],
}


# Export as default
default = moltbook_plugin
__all__ = ['moltbook_plugin', 'default']
