// Prompt Templates for Moltbook Content Generation
//
// Rust port of TypeScript templates module

use crate::types::{MoltbookPost, MoltbookComment};

/// Generate prompt template for post composition
pub fn get_post_template(
    character_name: &str,
    character_bio: &str,
    submolt: Option<&str>,
    recent_posts: &[MoltbookPost],
    topics: &[String],
) -> String {
    let mut parts = vec![
        format!("You are {}.", character_name),
        format!("About you: {}", character_bio),
        String::new(),
    ];
    
    if let Some(sub) = submolt {
        parts.push(format!("You're posting in the '{}' community.", sub));
    }
    
    if !topics.is_empty() {
        parts.push(format!("Hot topics: {}", topics.join(", ")));
    }
    
    if !recent_posts.is_empty() {
        parts.push(String::new());
        parts.push("Recent posts in this community:".to_string());
        for post in recent_posts.iter().take(3) {
            let author = post.author.username.as_str();
            parts.push(format!("- \"{}\" (by {})", post.title, author));
        }
    }
    
    parts.extend(vec![
        String::new(),
        "Write a thoughtful, engaging post that:".to_string(),
        "1. Adds value to the community".to_string(),
        "2. Shows your unique perspective".to_string(),
        "3. Fits the community's vibe".to_string(),
        "4. Is conversational and authentic".to_string(),
        String::new(),
        "Format: JSON with 'title' and 'content' fields.".to_string(),
        "Title: Compelling, specific, not clickbait (max 300 chars)".to_string(),
        "Content: Well-structured, insightful (max 10000 chars)".to_string(),
    ]);
    
    parts.join("\n")
}

/// Generate prompt template for comment composition
pub fn get_comment_template(
    character_name: &str,
    character_bio: &str,
    post: &MoltbookPost,
    parent_comment: Option<&MoltbookComment>,
) -> String {
    let mut parts = vec![
        format!("You are {}.", character_name),
        format!("About you: {}", character_bio),
        String::new(),
        format!("Post by {}:", post.author.username),
        format!("Title: {}", post.title),
    ];
    
    let content_preview = if post.content.len() > 500 {
        format!("{}...", &post.content[..500])
    } else {
        post.content.clone()
    };
    parts.push(format!("Content: {}", content_preview));
    parts.push(String::new());
    
    if let Some(parent) = parent_comment {
        parts.push(format!("Replying to comment by {}:", parent.author.username));
        parts.push(format!("\"{}\"", parent.content));
        parts.push(String::new());
    }
    
    parts.extend(vec![
        "Write a thoughtful comment that:".to_string(),
        "1. Responds directly to the content".to_string(),
        "2. Adds insight or asks good questions".to_string(),
        "3. Shows your personality".to_string(),
        "4. Is conversational and authentic".to_string(),
        String::new(),
        "Format: JSON with 'content' field.".to_string(),
        "Content: Engaging, substantive (max 5000 chars)".to_string(),
    ]);
    
    parts.join("\n")
}

/// Generate prompt for quality assessment
pub fn get_quality_judge_template(
    title: Option<&str>,
    content: &str,
    context: &str,
    is_comment: bool,
) -> String {
    let content_type = if is_comment { "comment" } else { "post" };
    
    let mut parts = vec![
        format!("Evaluate this {} for quality:", content_type),
        String::new(),
    ];
    
    if let Some(t) = title {
        if !is_comment {
            parts.push(format!("Title: {}", t));
        }
    }
    
    parts.extend(vec![
        format!("Content: {}", content),
        String::new(),
        format!("Context: {}", context),
        String::new(),
        "Rate on a scale of 1-10 for each criterion:".to_string(),
        "1. Relevance: Does it fit the community/conversation?".to_string(),
        "2. Interestingness: Would people want to read this?".to_string(),
        "3. Originality: Is this a fresh perspective?".to_string(),
        "4. Voice: Does it sound authentic and character-appropriate?".to_string(),
        "5. Value: Does it add something meaningful?".to_string(),
        String::new(),
        "Format: JSON with fields:".to_string(),
        "- relevance (1-10)".to_string(),
        "- interestingness (1-10)".to_string(),
        "- originality (1-10)".to_string(),
        "- voice (1-10)".to_string(),
        "- value (1-10)".to_string(),
        "- feedback (string explaining scores)".to_string(),
    ]);
    
    parts.join("\n")
}
