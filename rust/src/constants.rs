// Moltbook Plugin Constants
//
// Rust port of TypeScript constants from plugin-moltbook/typescript/src/constants.ts
//
// WHY CENTRALIZE CONSTANTS?
// 1. Single source of truth
// 2. Easy configuration
// 3. Documentation in code
// 4. Type safety with const

// =============================================================================
// API CONFIGURATION
// =============================================================================

/// Base URL for the Moltbook API
/// IMPORTANT: Must use www.moltbook.com! (redirects strip auth headers)
pub const MOLTBOOK_API_URL: &str = "https://www.moltbook.com/api/v1";

/// API endpoints
pub mod endpoints {
    use std::borrow::Cow;
    
    // Authentication / Agent Management
    pub const REGISTER: &str = "/agents/register";
    pub const ME: &str = "/agents/me";
    pub const STATUS: &str = "/agents/status";
    
    pub fn agent_profile(name: &str) -> String {
        format!("/agents/profile?name={}", urlencoding::encode(name))
    }
    
    pub fn agent_follow(name: &str) -> String {
        format!("/agents/{}/follow", urlencoding::encode(name))
    }
    
    // Posts
    pub const FEED: &str = "/feed";
    pub const POSTS: &str = "/posts";
    
    pub fn post_by_id(id: &str) -> String {
        format!("/posts/{}", id)
    }
    
    // Comments
    pub fn comments(post_id: &str) -> String {
        format!("/posts/{}/comments", post_id)
    }
    
    // Voting
    pub fn upvote(post_id: &str) -> String {
        format!("/posts/{}/upvote", post_id)
    }
    
    pub fn downvote(post_id: &str) -> String {
        format!("/posts/{}/downvote", post_id)
    }
    
    pub fn comment_upvote(comment_id: &str) -> String {
        format!("/comments/{}/upvote", comment_id)
    }
    
    pub fn comment_downvote(comment_id: &str) -> String {
        format!("/comments/{}/downvote", comment_id)
    }
    
    // Submolts
    pub const SUBMOLTS: &str = "/submolts";
    
    pub fn submolt_by_name(name: &str) -> String {
        format!("/submolts/{}", name)
    }
    
    pub fn submolt_feed(name: &str) -> String {
        format!("/submolts/{}/feed", name)
    }
    
    pub fn submolt_subscribe(name: &str) -> String {
        format!("/submolts/{}/subscribe", name)
    }
    
    // Search
    pub const SEARCH: &str = "/search";
}

// =============================================================================
// RATE LIMITS
// =============================================================================

// Global limits (IP-level)
pub const GLOBAL_REQUESTS_PER_MIN: usize = 200;
pub const GLOBAL_POSTS_PER_HOUR: usize = 20;

// Per-agent limits
pub const RATE_LIMIT_REQUESTS_PER_MIN: usize = 100;
pub const RATE_LIMIT_POST_INTERVAL_SEC: i64 = 30 * 60; // 30 minutes
pub const RATE_LIMIT_COMMENTS_PER_HOUR: usize = 50;

// Rate limit windows (milliseconds)
pub const RATE_LIMIT_REQUEST_WINDOW_MS: i64 = 60 * 1000;
pub const RATE_LIMIT_COMMENT_WINDOW_MS: i64 = 60 * 60 * 1000;

// =============================================================================
// CACHE CONFIGURATION
// =============================================================================

pub const CACHE_TTL_FEED_MS: i64 = 5 * 60 * 1000;      // 5 minutes
pub const CACHE_TTL_PROFILE_MS: i64 = 15 * 60 * 1000;  // 15 minutes
pub const CACHE_TTL_ANALYSIS_MS: i64 = 30 * 60 * 1000; // 30 minutes

// =============================================================================
// QUALITY THRESHOLDS
// =============================================================================

pub const MIN_QUALITY_SCORE_AUTONOMOUS: i32 = 7;
pub const MIN_QUALITY_SCORE_USER: i32 = 5;
pub const MAX_COMPOSE_RETRIES: i32 = 3;

// =============================================================================
// TASK CONFIGURATION
// =============================================================================

pub const MOLTBOOK_CYCLE_TASK: &str = "MOLTBOOK_CYCLE";
pub const CYCLE_INTERVAL_MS: i64 = 15 * 60 * 1000;     // 15 minutes
pub const MIN_AUTONOMOUS_POST_INTERVAL_MS: i64 = 60 * 60 * 1000; // 1 hour

// =============================================================================
// MEMORY KEYS
// =============================================================================

pub const CRED_MEMORY_KEY: &str = "moltbook_creds";
pub const COMMUNITY_ANALYSIS_KEY: &str = "moltbook_community_analysis";

// =============================================================================
// HTTP CONFIGURATION
// =============================================================================

pub const HTTP_TIMEOUT_MS: u64 = 30 * 1000;  // 30 seconds
pub const HTTP_MAX_RETRIES: usize = 3;
pub const HTTP_RETRY_BASE_DELAY_MS: u64 = 1000;

// =============================================================================
// CONTENT LIMITS
// =============================================================================

pub const MAX_TITLE_LENGTH: usize = 300;
pub const MAX_POST_LENGTH: usize = 40000;
pub const MAX_COMMENT_LENGTH: usize = 10000;

// =============================================================================
// PLUGIN METADATA
// =============================================================================

pub const PLUGIN_NAME: &str = "moltbook";
pub const PLUGIN_DESCRIPTION: &str = 
    "Moltbook social integration - community participation for AI agents";

// =============================================================================
// SERVICE CONFIGURATION
// =============================================================================

pub const MOLTBOOK_SERVICE_NAME: &str = "moltbook";

pub mod urls {
    pub const MOLTBOOK: &str = "https://www.moltbook.com/api/v1";
    pub const OPENROUTER: &str = "https://openrouter.ai/api/v1";
}

// =============================================================================
// AUTONOMY DEFAULTS
// =============================================================================

pub mod autonomy_defaults {
    pub const MIN_INTERVAL_MS: u64 = 30000;   // 30 seconds
    pub const MAX_INTERVAL_MS: u64 = 90000;   // 90 seconds
    pub const MAX_TOOL_CALLS: usize = 5;
    pub const DEFAULT_MODEL: &str = "deepseek/deepseek-chat-v3-0324";
}

// =============================================================================
// CONTENT LIMITS
// =============================================================================

pub mod content_limits {
    pub const DEFAULT_BROWSE_LIMIT: usize = 10;
    pub const MAX_CONTENT_LENGTH: usize = 10000;
    pub const MAX_TITLE_LENGTH: usize = 300;
    pub const MAX_COMMENT_LENGTH: usize = 5000;
}

// Default submolt
pub const DEFAULT_SUBMOLT: &str = "iq";

// =============================================================================
// MEMORY TABLE NAMES
// =============================================================================

pub mod memory_tables {
    pub const CREDENTIALS: &str = "moltbook_credentials";
    pub const POSTS_SEEN: &str = "moltbook_posts_seen";
    pub const INTERACTIONS: &str = "moltbook_interactions";
    pub const MOLTYS: &str = "moltbook_moltys";
    pub const OBSERVATIONS: &str = "moltbook_observations";
    pub const CULTURAL_LEARNINGS: &str = "moltbook_cultural_learnings";
    pub const NOTABLE_USERS: &str = "moltbook_notable_users";
    pub const MY_POSTS: &str = "moltbook_my_posts";
}
