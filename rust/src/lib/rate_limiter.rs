// Rate Limiter for Moltbook API
//
// TWO LEVELS OF RATE LIMITING:
// 1. GLOBAL (IP-level) - Shared across ALL agents
// 2. PER-AGENT - Each agent has their own limits
//
// Rust port of TypeScript rateLimiter

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};
use once_cell::sync::Lazy;

use crate::constants::*;
use crate::types::RateLimitState;

// =============================================================================
// GLOBAL RATE LIMITING (IP-level)
// =============================================================================

const GLOBAL_REQUEST_WINDOW_MS: i64 = 60 * 1000;  // 1 minute
const GLOBAL_POST_WINDOW_MS: i64 = 60 * 60 * 1000;  // 1 hour

#[derive(Debug, Clone)]
struct GlobalRateLimitState {
    requests: Vec<i64>,
    posts: Vec<i64>,
    retry_after: Option<i64>,
}

impl Default for GlobalRateLimitState {
    fn default() -> Self {
        Self {
            requests: Vec::new(),
            posts: Vec::new(),
            retry_after: None,
        }
    }
}

static GLOBAL_STATE: Lazy<Arc<Mutex<GlobalRateLimitState>>> = 
    Lazy::new(|| Arc::new(Mutex::new(GlobalRateLimitState::default())));

fn current_time_ms() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_millis() as i64
}

fn can_make_global_request() -> bool {
    let mut state = GLOBAL_STATE.lock().unwrap();
    
    // Check retry-after
    if let Some(retry_after) = state.retry_after {
        if current_time_ms() < retry_after {
            return false;
        }
    }
    
    // Prune old requests
    let cutoff = current_time_ms() - GLOBAL_REQUEST_WINDOW_MS;
    state.requests.retain(|&t| t > cutoff);
    
    state.requests.len() < GLOBAL_REQUESTS_PER_MIN
}

fn can_post_globally() -> bool {
    let mut state = GLOBAL_STATE.lock().unwrap();
    
    // Prune old posts
    let cutoff = current_time_ms() - GLOBAL_POST_WINDOW_MS;
    state.posts.retain(|&t| t > cutoff);
    
    state.posts.len() < GLOBAL_POSTS_PER_HOUR
}

fn record_global_request() {
    let mut state = GLOBAL_STATE.lock().unwrap();
    state.requests.push(current_time_ms());
}

fn record_global_post() {
    let mut state = GLOBAL_STATE.lock().unwrap();
    state.posts.push(current_time_ms());
}

pub fn set_global_retry_after(retry_after_seconds: i64) {
    let mut state = GLOBAL_STATE.lock().unwrap();
    state.retry_after = Some(current_time_ms() + retry_after_seconds * 1000);
}

// =============================================================================
// PER-AGENT RATE LIMITING
// =============================================================================

type AgentStates = Arc<Mutex<HashMap<String, RateLimitState>>>;

static AGENT_STATES: Lazy<AgentStates> = 
    Lazy::new(|| Arc::new(Mutex::new(HashMap::new())));

fn get_agent_state(agent_id: &str) -> RateLimitState {
    let mut states = AGENT_STATES.lock().unwrap();
    states
        .entry(agent_id.to_string())
        .or_insert_with(RateLimitState::default)
        .clone()
}

fn update_agent_state(agent_id: &str, state: RateLimitState) {
    let mut states = AGENT_STATES.lock().unwrap();
    states.insert(agent_id.to_string(), state);
}

fn prune_old_entries(entries: &[crate::types::RateLimitRequest], window_ms: i64) -> Vec<crate::types::RateLimitRequest> {
    let cutoff = current_time_ms() - window_ms;
    entries
        .iter()
        .filter(|e| e.timestamp > cutoff)
        .cloned()
        .collect()
}

pub fn can_make_request(agent_id: &str) -> bool {
    // Check global first
    if !can_make_global_request() {
        return false;
    }
    
    // Check per-agent
    let mut state = get_agent_state(agent_id);
    
    // Check retry-after
    if let Some(retry_after) = state.retry_after {
        if current_time_ms() < retry_after {
            return false;
        }
    }
    
    // Prune old requests
    state.requests = prune_old_entries(&state.requests, RATE_LIMIT_REQUEST_WINDOW_MS);
    update_agent_state(agent_id, state.clone());
    
    state.requests.len() < RATE_LIMIT_REQUESTS_PER_MIN
}

pub fn record_request(agent_id: &str) {
    record_global_request();
    
    let mut state = get_agent_state(agent_id);
    state.requests.push(crate::types::RateLimitRequest {
        timestamp: current_time_ms(),
    });
    update_agent_state(agent_id, state);
}

pub fn can_post(agent_id: &str) -> bool {
    if !can_make_request(agent_id) {
        return false;
    }
    
    if !can_post_globally() {
        return false;
    }
    
    let state = get_agent_state(agent_id);
    
    // Check last post time
    if let Some(last_post) = state.posts.last() {
        let elapsed = current_time_ms() - last_post.timestamp;
        if elapsed < RATE_LIMIT_POST_INTERVAL_SEC * 1000 {
            return false;
        }
    }
    
    true
}

pub fn record_post(agent_id: &str) {
    record_global_post();
    record_request(agent_id);
    
    let mut state = get_agent_state(agent_id);
    state.posts.push(crate::types::RateLimitRequest {
        timestamp: current_time_ms(),
    });
    update_agent_state(agent_id, state);
}

pub fn can_comment(agent_id: &str) -> bool {
    if !can_make_request(agent_id) {
        return false;
    }
    
    let mut state = get_agent_state(agent_id);
    state.comments = prune_old_entries(&state.comments, RATE_LIMIT_COMMENT_WINDOW_MS);
    update_agent_state(agent_id, state.clone());
    
    state.comments.len() < RATE_LIMIT_COMMENTS_PER_HOUR
}

pub fn record_comment(agent_id: &str) {
    record_request(agent_id);
    
    let mut state = get_agent_state(agent_id);
    state.comments.push(crate::types::RateLimitRequest {
        timestamp: current_time_ms(),
    });
    update_agent_state(agent_id, state);
}

pub fn get_time_until_can_post(agent_id: &str) -> i64 {
    let state = get_agent_state(agent_id);
    
    if let Some(last_post) = state.posts.last() {
        let elapsed = current_time_ms() - last_post.timestamp;
        let required = RATE_LIMIT_POST_INTERVAL_SEC * 1000;
        return std::cmp::max(0, required - elapsed);
    }
    
    0
}
