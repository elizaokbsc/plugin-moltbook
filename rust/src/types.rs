// Moltbook Plugin Type Definitions
// https://www.moltbook.com
//
// Rust port of TypeScript types from plugin-moltbook/typescript/src/types.ts

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

// =============================================================================
// API TYPES
// =============================================================================

/// A Moltbook user profile
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct MoltbookProfile {
    pub id: String,
    pub username: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub display_name: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub bio: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub avatar_url: Option<String>,
    pub created_at: String,
    pub follower_count: i32,
    pub following_count: i32,
    pub post_count: i32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub is_following: Option<bool>,
}

/// A Moltbook post (molty)
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct MoltbookPost {
    pub id: String,
    pub title: String,
    pub content: String,
    pub author_id: String,
    pub author: MoltbookProfile,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub submolt: Option<String>,
    pub created_at: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub updated_at: Option<String>,
    pub upvotes: i32,
    pub downvotes: i32,
    pub score: i32,
    pub comment_count: i32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub url: Option<String>,
}

/// A comment on a post
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct MoltbookComment {
    pub id: String,
    pub post_id: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub parent_id: Option<String>,
    pub content: String,
    pub author_id: String,
    pub author: MoltbookProfile,
    pub created_at: String,
    pub upvotes: i32,
    pub downvotes: i32,
    pub score: i32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub replies: Option<Vec<MoltbookComment>>,
}

/// A submolt (community/subreddit equivalent)
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct MoltbookSubmolt {
    pub id: String,
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    pub member_count: i32,
    pub post_count: i32,
    pub created_at: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub rules: Option<Vec<String>>,
}

/// Feed response from API
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct MoltbookFeed {
    pub posts: Vec<MoltbookPost>,
    pub has_more: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,
}

/// Search result item
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MoltbookSearchResult {
    pub id: String,
    #[serde(rename = "type")]
    pub result_type: String, // "post" or "comment"
    pub title: Option<String>,
    pub content: String,
    pub upvotes: i32,
    pub downvotes: i32,
    pub created_at: String,
    pub similarity: f32,
    pub author: HashMap<String, String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub submolt: Option<HashMap<String, String>>,
    pub post_id: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub post: Option<HashMap<String, String>>,
}

/// Search results from semantic search API
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MoltbookSearchResults {
    pub success: bool,
    pub query: String,
    #[serde(rename = "type")]
    pub search_type: String,
    pub results: Vec<MoltbookSearchResult>,
    pub count: usize,
}

// =============================================================================
// CREDENTIAL TYPES
// =============================================================================

/// Stored credentials for a Moltbook account
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct MoltbookCredentials {
    pub api_key: String,
    pub user_id: String,
    pub username: String,
    pub registered_at: i64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub claim_status: Option<String>, // "unclaimed" or "claimed"
    #[serde(skip_serializing_if = "Option::is_none")]
    pub claim_url: Option<String>,
}

// =============================================================================
// RATE LIMITING TYPES
// =============================================================================

/// Single rate limit request record
#[derive(Debug, Clone)]
pub struct RateLimitRequest {
    pub timestamp: i64,
}

/// Rate limit state per agent
#[derive(Debug, Clone)]
pub struct RateLimitState {
    pub requests: Vec<RateLimitRequest>,
    pub posts: Vec<RateLimitRequest>,
    pub comments: Vec<RateLimitRequest>,
    pub retry_after: Option<i64>,
}

impl Default for RateLimitState {
    fn default() -> Self {
        Self {
            requests: Vec::new(),
            posts: Vec::new(),
            comments: Vec::new(),
            retry_after: None,
        }
    }
}

// =============================================================================
// CACHE TYPES
// =============================================================================

/// Cached data with freshness tracking
#[derive(Debug, Clone)]
pub struct CachedData<T> {
    pub data: T,
    pub fetched_at: i64,
}

/// Cache options for fetch operations
#[derive(Debug, Clone, Default)]
pub struct CacheOptions {
    /// Maximum age in milliseconds
    pub max_age: Option<i64>,
    /// Require data newer than this timestamp
    pub newer_than: Option<i64>,
    /// Force fresh fetch, bypass cache
    pub force_fresh: bool,
}

/// Per-agent state including rate limits and cache
#[derive(Debug, Clone)]
pub struct AgentMoltbookState {
    pub credentials: Option<MoltbookCredentials>,
    pub rate_limits: RateLimitState,
    pub feed_cache: Option<CachedData<MoltbookFeed>>,
    pub profile_cache: Option<CachedData<MoltbookProfile>>,
}

impl Default for AgentMoltbookState {
    fn default() -> Self {
        Self {
            credentials: None,
            rate_limits: RateLimitState::default(),
            feed_cache: None,
            profile_cache: None,
        }
    }
}

// =============================================================================
// INTELLIGENCE TYPES
// =============================================================================

/// A specific engagement opportunity
#[derive(Debug, Clone)]
pub struct EngagementOpportunity {
    pub post: MoltbookPost,
    pub reason: String,
    pub engagement_type: String, // "comment", "upvote", or "follow"
    pub priority: i32,
}

/// Community analysis results
#[derive(Debug, Clone)]
pub struct CommunityContext {
    /// Hot topics being discussed
    pub active_topics: Vec<String>,
    /// Posts worth engaging with
    pub engagement_opportunities: Vec<EngagementOpportunity>,
    /// Posting patterns that work well
    pub what_works: Vec<String>,
    /// Notable community members
    pub notable_moltys: Vec<MoltbookProfile>,
    /// Overall community vibe
    pub vibe: String,
    /// When this analysis was generated
    pub analyzed_at: i64,
}

// =============================================================================
// QUALITY GATE TYPES
// =============================================================================

/// Quality assessment criteria
#[derive(Debug, Clone)]
pub struct QualityScore {
    pub relevance: i32,        // 1-10
    pub interestingness: i32,  // 1-10
    pub originality: i32,      // 1-10
    pub voice: i32,            // 1-10
    pub value: i32,            // 1-10
    pub overall: f32,          // Average
    pub feedback: String,
    pub pass: bool,
}

/// Content to be judged
#[derive(Debug, Clone)]
pub struct ContentToJudge {
    pub title: Option<String>,
    pub content: String,
    pub context: Option<String>,
    pub is_comment: bool,
}

// =============================================================================
// SERVICE CONFIGURATION
// =============================================================================

/// Service configuration
#[derive(Debug, Clone)]
pub struct MoltbookConfig {
    pub api_url: String,
    pub auto_register: bool,
    pub auto_engage: bool,
    pub min_quality_score: i32,
    pub max_compose_retries: i32,
}

impl Default for MoltbookConfig {
    fn default() -> Self {
        Self {
            api_url: "https://www.moltbook.com/api/v1".to_string(),
            auto_register: true,
            auto_engage: false,
            min_quality_score: 7,
            max_compose_retries: 3,
        }
    }
}

// =============================================================================
// RESULT TYPES
// =============================================================================

/// Result type for API operations
pub type MoltbookResult<T> = Result<T, MoltbookError>;

/// Helper to create successful result
pub fn moltbook_success<T>(data: T) -> MoltbookResult<T> {
    Ok(data)
}

/// Helper to create failed result
pub fn moltbook_failure<T>(error: String) -> MoltbookResult<T> {
    Err(MoltbookError::ApiError(error))
}

// =============================================================================
// ERROR TYPES
// =============================================================================

/// Moltbook error types
#[derive(Debug, thiserror::Error)]
pub enum MoltbookError {
    #[error("API error: {0}")]
    ApiError(String),
    
    #[error("Authentication error: {0}")]
    AuthenticationError(String),
    
    #[error("Rate limit error: {0}")]
    RateLimitError(String),
    
    #[error("Content too long: {0}")]
    ContentTooLongError(String),
    
    #[error("Configuration error: {0}")]
    ConfigurationError(String),
    
    #[error("Network error: {0}")]
    NetworkError(#[from] reqwest::Error),
    
    #[error("Serialization error: {0}")]
    SerializationError(#[from] serde_json::Error),
}

// =============================================================================
// POST WITH COMMENTS
// =============================================================================

/// Result of reading a post with its comments
#[derive(Debug, Clone)]
pub struct PostWithComments {
    pub post: MoltbookPost,
    pub comments: Vec<MoltbookComment>,
}
