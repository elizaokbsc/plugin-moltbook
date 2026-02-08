// Moltbook Actions
//
// Rust port of TypeScript actions from plugin-moltbook/typescript/src/actions/

use async_trait::async_trait;
use serde_json::json;
use std::any::Any;
use std::sync::Arc;

use crate::types::*;
use crate::constants::*;

// NOTE: This is a streamlined Rust port. Full ElizaOS action trait integration
// would require complete Rust runtime bindings which are out of scope for this port.
// These functions demonstrate the core action logic and can be wrapped in proper
// ElizaOS action structs when the Rust runtime is fully implemented.

// =============================================================================
// POST ACTION
// =============================================================================

/// Check if message indicates desire to post
pub fn should_post(message: &str) -> bool {
    let msg_lower = message.to_lowercase();
    msg_lower.contains("post") || 
    msg_lower.contains("share") || 
    msg_lower.contains("molty")
}

/// Validate post action
pub fn validate_post(message: &str) -> bool {
    should_post(message)
}

// =============================================================================
// COMMENT ACTION
// =============================================================================

/// Check if message indicates desire to comment
pub fn should_comment(message: &str) -> bool {
    let msg_lower = message.to_lowercase();
    msg_lower.contains("comment") || 
    msg_lower.contains("reply") || 
    msg_lower.contains("respond")
}

/// Validate comment action
pub fn validate_comment(message: &str) -> bool {
    should_comment(message)
}

// =============================================================================
// FOLLOW ACTION
// =============================================================================

/// Check if message indicates desire to follow/unfollow
pub fn should_follow(message: &str) -> bool {
    let msg_lower = message.to_lowercase();
    msg_lower.contains("follow") || msg_lower.contains("unfollow")
}

/// Parse follow intent from message
pub struct FollowIntent {
    pub username: String,
    pub unfollow: bool,
}

pub fn parse_follow_intent(message: &str) -> Option<FollowIntent> {
    let msg_lower = message.to_lowercase();
    let unfollow = msg_lower.contains("unfollow");
    
    // Extract username (simple heuristic: word after "follow" or last word)
    let words: Vec<&str> = message.split_whitespace().collect();
    
    if let Some(follow_idx) = words.iter().position(|&w| {
        w.to_lowercase().contains("follow")
    }) {
        if follow_idx + 1 < words.len() {
            let username = words[follow_idx + 1].trim_matches(|c: char| !c.is_alphanumeric());
            return Some(FollowIntent {
                username: username.to_string(),
                unfollow,
            });
        }
    }
    
    // Fallback: check for @username pattern
    for word in &words {
        if word.starts_with('@') {
            let username = word[1..].trim_matches(|c: char| !c.is_alphanumeric());
            if !username.is_empty() {
                return Some(FollowIntent {
                    username: username.to_string(),
                    unfollow,
                });
            }
        }
    }
    
    None
}

/// Validate follow action
pub fn validate_follow(message: &str) -> bool {
    should_follow(message) && parse_follow_intent(message).is_some()
}

// =============================================================================
// VOTE ACTION
// =============================================================================

/// Check if message indicates desire to vote
pub fn should_vote(message: &str) -> bool {
    let msg_lower = message.to_lowercase();
    msg_lower.contains("upvote") || 
    msg_lower.contains("downvote") || 
    (msg_lower.contains("vote") && (msg_lower.contains("up") || msg_lower.contains("down")))
}

/// Parse vote intent from message
pub struct VoteIntent {
    pub target_id: String,
    pub vote_type: String, // "up" or "down"
    pub is_comment: bool,
}

pub fn parse_vote_intent(message: &str) -> Option<VoteIntent> {
    let msg_lower = message.to_lowercase();
    let vote_type = if msg_lower.contains("downvote") || 
                       (msg_lower.contains("vote") && msg_lower.contains("down")) {
        "down"
    } else {
        "up"
    };
    
    let is_comment = msg_lower.contains("comment");
    
    // Extract ID - look for patterns like "post 123" or "comment abc"
    let words: Vec<&str> = message.split_whitespace().collect();
    
    for (i, word) in words.iter().enumerate() {
        let w_lower = word.to_lowercase();
        if (w_lower == "post" || w_lower == "comment") && i + 1 < words.len() {
            let id = words[i + 1].trim_matches(|c: char| !c.is_alphanumeric());
            if !id.is_empty() {
                return Some(VoteIntent {
                    target_id: id.to_string(),
                    vote_type: vote_type.to_string(),
                    is_comment: w_lower == "comment",
                });
            }
        }
    }
    
    None
}

/// Validate vote action
pub fn validate_vote(message: &str) -> bool {
    should_vote(message) && parse_vote_intent(message).is_some()
}

// =============================================================================
// SEARCH ACTION
// =============================================================================

/// Check if message indicates desire to search
pub fn should_search(message: &str) -> bool {
    let msg_lower = message.to_lowercase();
    msg_lower.contains("search") || 
    msg_lower.contains("find") || 
    msg_lower.contains("look for")
}

/// Parse search intent from message
pub struct SearchIntent {
    pub query: String,
    pub search_type: String, // "post", "comment", or "all"
}

pub fn parse_search_intent(message: &str) -> Option<SearchIntent> {
    let msg_lower = message.to_lowercase();
    
    // Determine search type
    let search_type = if msg_lower.contains("comment") {
        "comment"
    } else if msg_lower.contains("post") {
        "post"
    } else {
        "all"
    };
    
    // Extract query - everything after "search for", "find", etc.
    let patterns = ["search for", "find", "look for", "search"];
    
    for pattern in &patterns {
        if let Some(idx) = msg_lower.find(pattern) {
            let query_start = idx + pattern.len();
            let query = message[query_start..]
                .trim()
                .trim_matches(|c: char| c == '"' || c == '\'')
                .to_string();
            
            if !query.is_empty() {
                return Some(SearchIntent {
                    query,
                    search_type: search_type.to_string(),
                });
            }
        }
    }
    
    None
}

/// Validate search action
pub fn validate_search(message: &str) -> bool {
    should_search(message) && parse_search_intent(message).is_some()
}

// =============================================================================
// ACTION METADATA
// =============================================================================

pub struct ActionMetadata {
    pub name: &'static str,
    pub description: &'static str,
    pub examples: Vec<Vec<(&'static str, &'static str)>>,
}

pub const POST_ACTION: ActionMetadata = ActionMetadata {
    name: "MOLTBOOK_POST",
    description: "Create a new post on Moltbook",
    examples: vec![
        vec![
            ("user", "Post about AI on Moltbook"),
            ("assistant", "I'll create a post about AI..."),
        ],
        vec![
            ("user", "Share this thought on Moltbook: ..."),
            ("assistant", "Posting to Moltbook..."),
        ],
    ],
};

pub const COMMENT_ACTION: ActionMetadata = ActionMetadata {
    name: "MOLTBOOK_COMMENT",
    description: "Comment on a Moltbook post",
    examples: vec![
        vec![
            ("user", "Comment on post 123"),
            ("assistant", "I'll add a thoughtful comment..."),
        ],
    ],
};

pub const FOLLOW_ACTION: ActionMetadata = ActionMetadata {
    name: "MOLTBOOK_FOLLOW",
    description: "Follow or unfollow a Moltbook user",
    examples: vec![
        vec![
            ("user", "Follow @alice on Moltbook"),
            ("assistant", "Following alice..."),
        ],
        vec![
            ("user", "Unfollow bob"),
            ("assistant", "Unfollowing bob..."),
        ],
    ],
};

pub const VOTE_ACTION: ActionMetadata = ActionMetadata {
    name: "MOLTBOOK_VOTE",
    description: "Vote on Moltbook posts or comments",
    examples: vec![
        vec![
            ("user", "Upvote post 123"),
            ("assistant", "Upvoting post..."),
        ],
        vec![
            ("user", "Downvote comment abc"),
            ("assistant", "Downvoting comment..."),
        ],
    ],
};

pub const SEARCH_ACTION: ActionMetadata = ActionMetadata {
    name: "MOLTBOOK_SEARCH",
    description: "Search Moltbook posts and comments",
    examples: vec![
        vec![
            ("user", "Search Moltbook for AI agents"),
            ("assistant", "Searching for 'AI agents'..."),
        ],
    ],
};
