"""
Content Quality Assessment

Judges content against multiple criteria to ensure quality posts.

Python port of TypeScript judge from plugin-moltbook/typescript/src/lib/judge.ts
"""

import json
import logging
from typing import Any, Optional
from ..types import QualityScore, ContentToJudge
from .templates import get_quality_judge_template

logger = logging.getLogger(__name__)


async def judge_content(
    content_to_judge: ContentToJudge,
    llm_generate_fn: Any
) -> Optional[QualityScore]:
    """
    Judge content quality across multiple dimensions
    
    Args:
        content_to_judge: Content to evaluate
        llm_generate_fn: Async function that calls LLM with a prompt
    
    Returns:
        QualityScore if successful, None otherwise
    """
    
    prompt = get_quality_judge_template(
        title=content_to_judge.title,
        content=content_to_judge.content,
        context=content_to_judge.context or "",
        is_comment=content_to_judge.isComment
    )
    
    try:
        logger.debug("Judging content quality")
        
        # Get LLM assessment
        response = await llm_generate_fn(prompt)
        
        # Parse JSON response
        try:
            result = json.loads(response)
            
            relevance = int(result.get('relevance', 5))
            interestingness = int(result.get('interestingness', 5))
            originality = int(result.get('originality', 5))
            voice = int(result.get('voice', 5))
            value = int(result.get('value', 5))
            feedback = result.get('feedback', '')
            
            # Calculate overall score (average)
            overall = (relevance + interestingness + originality + voice + value) / 5.0
            
            # Determine pass/fail (>= 5 is pass)
            pass_threshold = 5.0
            passes = overall >= pass_threshold
            
            quality = QualityScore(
                relevance=relevance,
                interestingness=interestingness,
                originality=originality,
                voice=voice,
                value=value,
                overall=overall,
                feedback=feedback,
                pass_=passes
            )
            
            logger.info(f"Quality assessment: {overall:.1f}/10 ({'PASS' if passes else 'FAIL'})")
            logger.debug(f"Scores - R:{relevance} I:{interestingness} O:{originality} V:{voice} Val:{value}")
            
            return quality
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse quality assessment: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Error judging content: {e}")
        return None


def format_quality_feedback(quality: QualityScore) -> str:
    """Format quality score into human-readable feedback"""
    
    lines = [
        f"Quality Score: {quality.overall:.1f}/10 ({'✓ PASS' if quality.pass_ else '✗ FAIL'})",
        "",
        f"Relevance:        {quality.relevance}/10",
        f"Interestingness:  {quality.interestingness}/10",
        f"Originality:      {quality.originality}/10",
        f"Voice:            {quality.voice}/10",
        f"Value:            {quality.value}/10",
        "",
        "Feedback:",
        quality.feedback
    ]
    
    return "\n".join(lines)
