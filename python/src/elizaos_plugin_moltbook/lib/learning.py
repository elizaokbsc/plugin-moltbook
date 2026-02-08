"""
Learning and Memory System

Stores observations, cultural learnings, and notable users for continuous improvement.

Python port of TypeScript learning from plugin-moltbook/typescript/src/lib/learning.ts
"""

import logging
from typing import Any, Dict, List, Optional
from ..constants import MEMORY_TABLES

logger = logging.getLogger(__name__)


# Type aliases for memory store functions
# In real implementation, these would be passed from runtime
MemoryStore = Any


async def store_observation(
    runtime: Any,
    observation: str,
    context: Optional[str] = None
) -> bool:
    """
    Store an observation for future reference
    
    Args:
        runtime: AgentRuntime with memory access
        observation: The observation to store
        context: Optional context about the observation
    
    Returns:
        True if stored successfully
    """
    try:
        memory_data = {
            'type': 'moltbook_observation',
            'observation': observation,
            'context': context,
            'timestamp': int(__import__('time').time() * 1000)
        }
        
        # Store in memory (implementation depends on runtime API)
        # await runtime.memory.create(MEMORY_TABLES.OBSERVATIONS, memory_data)
        
        logger.debug(f"Stored observation: {observation[:50]}...")
        return True
        
    except Exception as e:
        logger.error(f"Failed to store observation: {e}")
        return False


async def store_cultural_learning(
    runtime: Any,
    learning: str,
    submolt: Optional[str] = None
) -> bool:
    """
    Store a cultural learning about the community
    
    Args:
        runtime: AgentRuntime with memory access
        learning: The cultural insight learned
        submolt: Submolt this learning applies to
    
    Returns:
        True if stored successfully
    """
    try:
        memory_data = {
            'type': 'moltbook_cultural_learning',
            'learning': learning,
            'submolt': submolt,
            'timestamp': int(__import__('time').time() * 1000)
        }
        
        # Store in memory
        # await runtime.memory.create(MEMORY_TABLES.CULTURAL_LEARNINGS, memory_data)
        
        logger.debug(f"Stored cultural learning: {learning[:50]}...")
        return True
        
    except Exception as e:
        logger.error(f"Failed to store cultural learning: {e}")
        return False


async def remember_notable_user(
    runtime: Any,
    username: str,
    reason: str,
    profile_data: Optional[Dict] = None
) -> bool:
    """
    Remember a notable community member
    
    Args:
        runtime: AgentRuntime with memory access
        username: Username of the notable user
        reason: Why this user is notable
        profile_data: Optional profile information
    
    Returns:
        True if stored successfully
    """
    try:
        memory_data = {
            'type': 'moltbook_notable_user',
            'username': username,
            'reason': reason,
            'profile': profile_data or {},
            'timestamp': int(__import__('time').time() * 1000)
        }
        
        # Store in memory
        # await runtime.memory.create(MEMORY_TABLES.NOTABLE_USERS, memory_data)
        
        logger.debug(f"Remembered notable user: {username}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to remember notable user: {e}")
        return False


async def get_cultural_learnings(
    runtime: Any,
    submolt: Optional[str] = None,
    limit: int = 10
) -> List[Dict]:
    """
    Retrieve cultural learnings
    
    Args:
        runtime: AgentRuntime with memory access
        submolt: Filter by submolt
        limit: Maximum number to retrieve
    
    Returns:
        List of cultural learning records
    """
    try:
        # Query memory
        # learnings = await runtime.memory.query(
        #     table=MEMORY_TABLES.CULTURAL_LEARNINGS,
        #     filters={'submolt': submolt} if submolt else {},
        #     limit=limit
        # )
        
        # Placeholder return
        learnings = []
        
        logger.debug(f"Retrieved {len(learnings)} cultural learnings")
        return learnings
        
    except Exception as e:
        logger.error(f"Failed to retrieve cultural learnings: {e}")
        return []


async def get_notable_users(
    runtime: Any,
    limit: int = 10
) -> List[Dict]:
    """
    Retrieve notable users
    
    Args:
        runtime: AgentRuntime with memory access
        limit: Maximum number to retrieve
    
    Returns:
        List of notable user records
    """
    try:
        # Query memory
        # users = await runtime.memory.query(
        #     table=MEMORY_TABLES.NOTABLE_USERS,
        #     limit=limit
        # )
        
        # Placeholder return
        users = []
        
        logger.debug(f"Retrieved {len(users)} notable users")
        return users
        
    except Exception as e:
        logger.error(f"Failed to retrieve notable users: {e}")
        return []


async def get_recent_observations(
    runtime: Any,
    limit: int = 20
) -> List[Dict]:
    """
    Retrieve recent observations
    
    Args:
        runtime: AgentRuntime with memory access
        limit: Maximum number to retrieve
    
    Returns:
        List of observation records
    """
    try:
        # Query memory
        # observations = await runtime.memory.query(
        #     table=MEMORY_TABLES.OBSERVATIONS,
        #     limit=limit,
        #     sort_by='timestamp',
        #     sort_order='desc'
        # )
        
        # Placeholder return
        observations = []
        
        logger.debug(f"Retrieved {len(observations)} observations")
        return observations
        
    except Exception as e:
        logger.error(f"Failed to retrieve observations: {e}")
        return []


async def get_learnings_summary(runtime: Any) -> str:
    """
    Generate a summary of all learnings
    
    Args:
        runtime: AgentRuntime with memory access
    
    Returns:
        Formatted summary string
    """
    try:
        cultural = await get_cultural_learnings(runtime, limit=5)
        users = await get_notable_users(runtime, limit=5)
        observations = await get_recent_observations(runtime, limit=10)
        
        lines = ["## Learnings Summary", ""]
        
        if cultural:
            lines.append("**Cultural Insights**:")
            for item in cultural:
                learning = item.get('learning', '')
                lines.append(f"- {learning}")
            lines.append("")
        
        if users:
            lines.append("**Notable Community Members**:")
            for item in users:
                username = item.get('username', 'Unknown')
                reason = item.get('reason', '')
                lines.append(f"- @{username}: {reason}")
            lines.append("")
        
        if observations:
            lines.append("**Recent Observations**:")
            for item in observations[:5]:
                obs = item.get('observation', '')
                lines.append(f"- {obs}")
            lines.append("")
        
        if not cultural and not users and not observations:
            lines.append("No learnings recorded yet.")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Failed to generate learnings summary: {e}")
        return "Error generating learnings summary"


def format_cultural_learnings(learnings: List[Dict]) -> str:
    """Format cultural learnings into readable string"""
    if not learnings:
        return "No cultural learnings yet."
    
    lines = []
    for item in learnings:
        learning = item.get('learning', '')
        submolt = item.get('submolt', 'general')
        lines.append(f"[{submolt}] {learning}")
    
    return "\n".join(lines)


def format_notable_users(users: List[Dict]) -> str:
    """Format notable users into readable string"""
    if not users:
        return "No notable users remembered yet."
    
    lines = []
    for item in users:
        username = item.get('username', 'Unknown')
        reason = item.get('reason', '')
        lines.append(f"@{username}: {reason}")
    
    return "\n".join(lines)
