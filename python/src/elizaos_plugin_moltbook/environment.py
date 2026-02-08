"""
Environment Settings Management

Python port of TypeScript environment module
"""

import os
import logging
from typing import Optional
from .types import MoltbookSettings

logger = logging.getLogger(__name__)


def get_moltbook_settings(runtime: Optional[any] = None) -> MoltbookSettings:
    """
    Get Moltbook settings from environment/runtime
    
    Args:
        runtime: Optional AgentRuntime with getSetting method
    
    Returns:
        MoltbookSettings with configuration
    """
    
    def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
        """Get setting from runtime or environment"""
        if runtime and hasattr(runtime, 'get_setting'):
            return runtime.get_setting(key, default)
        return os.getenv(key, default)
    
    # Get agent name
    agent_name = "Agent"
    if runtime and hasattr(runtime, 'character') and hasattr(runtime.character, 'name'):
        agent_name = runtime.character.name
    
    return MoltbookSettings(
        agentName=agent_name,
        moltbookToken=get_setting('MOLTBOOK_API_KEY'),
        llmApiKey=get_setting('LLM_API_KEY') or get_setting('OPENAI_API_KEY'),
        llmBaseUrl=get_setting('LLM_BASE_URL'),
        model=get_setting('LLM_MODEL'),
        personality=get_setting('AGENT_PERSONALITY'),
        autonomyIntervalMs=int(get_setting('MOLTBOOK_AUTONOMY_INTERVAL_MS', '900000')),  # 15 min default
        autonomyMaxSteps=int(get_setting('MOLTBOOK_AUTONOMY_MAX_STEPS', '100')),
        autonomousMode=get_setting('MOLTBOOK_AUTO_ENGAGE', 'false').lower() == 'true'
    )


def validate_moltbook_settings(settings: MoltbookSettings) -> tuple[bool, Optional[str]]:
    """
    Validate Moltbook settings
    
    Args:
        settings: Settings to validate
    
    Returns:
        (is_valid, error_message) tuple
    """
    
    # Check required settings
    if not settings.agentName:
        return (False, "Agent name is required")
    
    # Optional but recommended checks
    warnings = []
    
    if not settings.moltbookToken:
        warnings.append("No MOLTBOOK_API_KEY set - will auto-register")
    
    if settings.autonomousMode and not settings.llmApiKey:
        warnings.append("Autonomous mode enabled but no LLM API key set")
    
    # Log warnings
    for warning in warnings:
        logger.warning(f"Moltbook settings: {warning}")
    
    return (True, None)
