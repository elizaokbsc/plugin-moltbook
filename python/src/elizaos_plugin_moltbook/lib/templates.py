"""
Prompt Templates for Moltbook Content Generation

Python port of TypeScript templates from plugin-moltbook/typescript/src/lib/templates.ts
"""

from typing import List, Optional
from ..types import MoltbookPost, Moltbook

Comment


def get_post_template(
    character_name: str,
    character_bio: str,
    submolt: Optional[str],
    recent_posts: List[MoltbookPost],
    topics: List[str]
) -> str:
    """Generate prompt template for post composition"""
    
    context_parts = [
        f"You are {character_name}.",
        f"About you: {character_bio}",
        ""
    ]
    
    if submolt:
        context_parts.append(f"You're posting in the '{submolt}' community.")
    
    if topics:
        context_parts.append(f"Hot topics: {', '.join(topics)}")
    
    if recent_posts:
        context_parts.append("\nRecent posts in this community:")
        for post in recent_posts[:3]:
            context_parts.append(f"- \"{post.get('title', '')}\" (by {post.get('author', {}).get('username', 'unknown')})")
    
    context_parts.extend([
        "",
        "Write a thoughtful, engaging post that:",
        "1. Adds value to the community",
        "2. Shows your unique perspective",
        "3. Fits the community's vibe",
        "4. Is conversational and authentic",
        "",
        "Format: JSON with 'title' and 'content' fields.",
        "Title: Compelling, specific, not clickbait (max 300 chars)",
        "Content: Well-structured, insightful (max 10000 chars)",
    ])
    
    return "\n".join(context_parts)


def get_comment_template(
    character_name: str,
    character_bio: str,
    post: MoltbookPost,
    parent_comment: Optional[MoltbookComment] = None
) -> str:
    """Generate prompt template for comment composition"""
    
    post_title = post.get('title', '')
    post_content = post.get('content', '')
    post_author = post.get('author', {}).get('username', 'unknown')
    
    context_parts = [
        f"You are {character_name}.",
        f"About you: {character_bio}",
        "",
        f"Post by {post_author}:",
        f"Title: {post_title}",
        f"Content: {post_content[:500]}{'...' if len(post_content) > 500 else ''}",
        ""
    ]
    
    if parent_comment:
        parent_author = parent_comment.get('author', {}).get('username', 'unknown')
        parent_content = parent_comment.get('content', '')
        context_parts.extend([
            f"Replying to comment by {parent_author}:",
            f"\"{parent_content}\"",
            ""
        ])
    
    context_parts.extend([
        "Write a thoughtful comment that:",
        "1. Responds directly to the content",
        "2. Adds insight or asks good questions",
        "3. Shows your personality",
        "4. Is conversational and authentic",
        "",
        "Format: JSON with 'content' field.",
        "Content: Engaging, substantive (max 5000 chars)",
    ])
    
    return "\n".join(context_parts)


def get_quality_judge_template(
    title: Optional[str],
    content: str,
    context: str,
    is_comment: bool
) -> str:
    """Generate prompt for quality assessment"""
    
    content_type = "comment" if is_comment else "post"
    
    template_parts = [
        f"Evaluate this {content_type} for quality:",
        ""
    ]
    
    if title and not is_comment:
        template_parts.append(f"Title: {title}")
    
    template_parts.extend([
        f"Content: {content}",
        "",
        f"Context: {context}",
        "",
        "Rate on a scale of 1-10 for each criterion:",
        "1. Relevance: Does it fit the community/conversation?",
        "2. Interestingness: Would people want to read this?",
        "3. Originality: Is this a fresh perspective?",
        "4. Voice: Does it sound authentic and character-appropriate?",
        "5. Value: Does it add something meaningful?",
        "",
        "Format: JSON with fields:",
        "- relevance (1-10)",
        "- interestingness (1-10)",
        "- originality (1-10)",
        "- voice (1-10)",
        "- value (1-10)",
        "- feedback (string explaining scores and suggesting improvements)",
    ])
    
    return "\n".join(template_parts)


def get_community_analysis_template(
    posts: List[MoltbookPost],
    character_name: str
) -> str:
    """Generate prompt for community analysis"""
    
    template_parts = [
        f"You are {character_name}, analyzing the Moltbook community.",
        "",
        "Recent posts:",
        ""
    ]
    
    for i, post in enumerate(posts[:10], 1):
        title = post.get('title', '')
        author = post.get('author', {}).get('username', 'unknown')
        score = post.get('score', 0)
        comments = post.get('commentCount', 0)
        template_parts.append(f"{i}. \"{title}\" by {author} ({score}↑, {comments} comments)")
    
    template_parts.extend([
        "",
        "Analyze and provide:",
        "1. Active topics (3-5 trending themes)",
        "2. Community vibe (overall tone/culture)",
        "3. What works (successful post patterns)",
        "4. Engagement opportunities (which posts to engage with and why)",
        "",
        "Format: JSON with fields:",
        "- activeTopics: string[]",
        "- vibe: string",
        "- whatWorks: string[]",
        "- engagementOpportunities: {postId: string, reason: string, type: 'comment'|'upvote', priority: number}[]",
    ])
    
    return "\n".join(template_parts)


def get_reflection_template(
    interaction_type: str,
    content: str,
    outcome: str,
    character_name: str
) -> str:
    """Generate prompt for post-interaction reflection"""
    
    return f"""You are {character_name}, reflecting on a recent Moltbook interaction.

Interaction: {interaction_type}
What you did: {content}
Outcome: {outcome}

Reflect on:
1. What worked well?
2. What could be improved?
3. What did you learn about the community?
4. How will this inform future interactions?

Format: JSON with fields:
- learnings: string[] (key takeaways)
- improvements: string[] (how to do better)
- cultural_insights: string[] (community norms/patterns observed)
"""
