"""
Reflection Evaluator

Post-interaction learning and reflection.

Python port of TypeScript reflection evaluator
"""

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def should_evaluate_reflection(runtime: Any, message: Any, state: Optional[Any] = None) -> bool:
    """Determine if reflection should run"""
    # Run reflection after Moltbook interactions
    if hasattr(message, 'content') and hasattr(message.content, 'action'):
        action = message.content.action
        moltbook_actions = [
            'MOLTBOOK_POST',
            'MOLTBOOK_COMMENT',
            'MOLTBOOK_FOLLOW',
            'MOLTBOOK_VOTE'
        ]
        return action in moltbook_actions
    return False


async def evaluate_reflection(
    runtime: Any,
    message: Any,
    state: Optional[Any],
    didRespond: bool
) -> None:
    """
    Evaluate and learn from a recent interaction
    
    Args:
        runtime: AgentRuntime
        message: The message/interaction
        state: Current state
        didRespond: Whether agent responded
    """
    try:
        if not did Respond:
            return
        
        logger.debug("Running reflection evaluator")
        
        # Extract interaction details
        action = getattr(message.content, 'action', 'unknown')
        text = getattr(message.content, 'text', '')
        
        # Get interaction outcome from state if available
        outcome = "completed"
        if state:
            outcome = state.get('outcome', 'completed')
        
        # Generate reflection prompt
        from ..lib.templates import get_reflection_template
        prompt = get_reflection_template(
            interaction_type=action,
            content=text[:500],  # Truncate for context
            outcome=outcome,
            character_name=runtime.character.name if hasattr(runtime, 'character') else "Agent"
        )
        
        # Get LLM reflection (if available)
        if hasattr(runtime, 'generate_text'):
            try:
                response = await runtime.generate_text(prompt)
                result = json.loads(response)
                
                # Extract learnings
                learnings = result.get('learnings', [])
                improvements = result.get('improvements', [])
                cultural_insights = result.get('cultural_insights', [])
                
                # Store learnings in memory
                from ..lib.learning import store_observation, store_cultural_learning
                
                for learning in learnings:
                    await store_observation(runtime, learning, context=action)
                
                for insight in cultural_insights:
                    await store_cultural_learning(runtime, insight)
                
                logger.info(f"Reflection complete: {len(learnings)} learnings, {len(cultural_insights)} insights")
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse reflection response")
            except Exception as e:
                logger.error(f"Error generating reflection: {e}")
        else:
            # Fallback: Simple heuristic learning
            await _simple_reflection(runtime, action, text, outcome)
        
    except Exception as e:
        logger.error(f"Error in reflection evaluator: {e}")


async def _simple_reflection(runtime: Any, action: str, text: str, outcome: str) -> None:
    """Simple heuristic-based reflection (fallback)"""
    try:
        from ..lib.learning import store_observation
        
        # Generate simple observation
        observation = f"Performed {action} - {outcome}"
        await store_observation(runtime, observation, context=action)
        
        logger.debug(f"Simple reflection stored: {observation}")
        
    except Exception as e:
        logger.error(f"Error in simple reflection: {e}")


# Evaluator definition for plugin registration
REFLECTION_EVALUATOR = {
    'name': 'MOLTBOOK_REFLECTION',
    'description': 'Learn from Moltbook interactions and refine future behavior',
    'validate': should_evaluate_reflection,
    'handler': evaluate_reflection,
    'examples': []
}
