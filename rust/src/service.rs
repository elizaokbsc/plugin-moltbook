//! Moltbook Service
//!
//! Core service managing Moltbook integration including:
//! - Credential management (ENV > Memory > Auto-register)
//! - Rate limiting and request tracking
//! - Caching for feed, profile, and community analysis
//! - API client integration
//!
//! Rust port of TypeScript service implementation

use std::sync::{Arc, Mutex};
use std::collections::HashMap;

use crate::constants::*;
use crate::types::*;
use crate::lib::{MoltbookApiClient, rate_limiter};

/// Main Moltbook service
pub struct MoltbookService {
    config: MoltbookConfig,
    api_client: MoltbookApiClient,
    agent_states: Arc<Mutex<HashMap<String, AgentMoltbookState>>>,
}

impl MoltbookService {
    /// Create a new Moltbook service
    pub fn new(config: MoltbookConfig) -> Self {
        Self {
            config,
            api_client: MoltbookApiClient::new(),
            agent_states: Arc::new(Mutex::new(HashMap::new())),
        }
    }
    
    /// Get or create agent state
    fn get_agent_state(&self, agent_id: &str) -> AgentMoltbookState {
        let mut states = self.agent_states.lock().unwrap();
        states
            .entry(agent_id.to_string())
            .or_insert_with(AgentMoltbookState::default)
            .clone()
    }
    
    /// Update agent state
    fn update_agent_state(&self, agent_id: &str, state: AgentMoltbookState) {
        let mut states = self.agent_states.lock().unwrap();
        states.insert(agent_id.to_string(), state);
    }
    
    /// Get credentials for an agent
    ///
    /// Order: ENV vars > Memory > Auto-register (if enabled)
    pub async fn get_credentials(&self, agent_id: &str) -> MoltbookResult<MoltbookCredentials> {
        // Check agent state first (in-memory cache)
        let state = self.get_agent_state(agent_id);
        if let Some(creds) = state.credentials {
            return Ok(creds);
        }
        
        // TODO: Check memory storage when Rust runtime integration is complete
        // let memory_creds = self.load_credentials_from_memory(agent_id).await?;
        // if let Some(creds) = memory_creds {
        //     return Ok(creds);
        // }
        
        // Auto-register if enabled
        if self.config.auto_register {
            let creds = self.api_client.register_agent(
                agent_id,
                &format!("agent-{}", agent_id),
                "An AI agent powered by ElizaOS",
            ).await?;
            
            // Store credentials
            let mut state = self.get_agent_state(agent_id);
            state.credentials = Some(creds.clone());
            self.update_agent_state(agent_id, state);
            
            // TODO: Save to memory when runtime integration is complete
            // self.save_credentials_to_memory(agent_id, &creds).await?;
            
            return Ok(creds);
        }
        
        Err(MoltbookError::AuthenticationError(
            "No credentials found and auto-register disabled".to_string()
        ))
    }
    
    /// Get feed with caching
    pub async fn get_feed(
        &self,
        agent_id: &str,
        submolt: Option<&str>,
        sort: &str,
        limit: usize,
        cache_opts: Option<CacheOptions>,
    ) -> MoltbookResult<MoltbookFeed> {
        let creds = self.get_credentials(agent_id).await?;
        
        // Check cache
        let state = self.get_agent_state(agent_id);
        if let Some(cached) = &state.feed_cache {
            let age = current_time_ms() - cached.fetched_at;
            let max_age = cache_opts.as_ref()
                .and_then(|opts| opts.max_age)
                .unwrap_or(CACHE_TTL_FEED_MS);
            
            let force_fresh = cache_opts.as_ref()
                .map(|opts| opts.force_fresh)
                .unwrap_or(false);
            
            if !force_fresh && age < max_age {
                return Ok(cached.data.clone());
            }
        }
        
        // Fetch fresh data
        let feed = self.api_client.get_posts(
            agent_id,
            &creds.api_key,
            submolt,
            sort,
            limit,
        ).await?;
        
        // Update cache
        let mut state = self.get_agent_state(agent_id);
        state.feed_cache = Some(CachedData {
            data: feed.clone(),
            fetched_at: current_time_ms(),
        });
        self.update_agent_state(agent_id, state);
        
        Ok(feed)
    }
    
    /// Create a post
    pub async fn create_post(
        &self,
        agent_id: &str,
        title: &str,
        content: &str,
        submolt: Option<&str>,
    ) -> MoltbookResult<MoltbookPost> {
        // Validate content length
        if title.len() > MAX_TITLE_LENGTH {
            return Err(MoltbookError::ContentTooLongError(
                format!("Title exceeds {} characters", MAX_TITLE_LENGTH)
            ));
        }
        if content.len() > MAX_POST_LENGTH {
            return Err(MoltbookError::ContentTooLongError(
                format!("Content exceeds {} characters", MAX_POST_LENGTH)
            ));
        }
        
        // Check rate limits
        if !rate_limiter::can_post(agent_id) {
            return Err(MoltbookError::RateLimitError(
                "Cannot post - rate limit exceeded".to_string()
            ));
        }
        
        let creds = self.get_credentials(agent_id).await?;
        
        self.api_client.create_post(
            agent_id,
            &creds.api_key,
            title,
            content,
            submolt,
        ).await
    }
    
    /// Create a comment
    pub async fn create_comment(
        &self,
        agent_id: &str,
        post_id: &str,
        content: &str,
        parent_id: Option<&str>,
    ) -> MoltbookResult<MoltbookComment> {
        // Validate content length
        if content.len() > MAX_COMMENT_LENGTH {
            return Err(MoltbookError::ContentTooLongError(
                format!("Comment exceeds {} characters", MAX_COMMENT_LENGTH)
            ));
        }
        
        // Check rate limits
        if !rate_limiter::can_comment(agent_id) {
            return Err(MoltbookError::RateLimitError(
                "Cannot comment - rate limit exceeded".to_string()
            ));
        }
        
        let creds = self.get_credentials(agent_id).await?;
        
        self.api_client.create_comment(
            agent_id,
            &creds.api_key,
            post_id,
            content,
            parent_id,
        ).await
    }
    
    /// Get comments for a post
    pub async fn get_comments(
        &self,
        agent_id: &str,
        post_id: &str,
    ) -> MoltbookResult<Vec<MoltbookComment>> {
        let creds = self.get_credentials(agent_id).await?;
        
        self.api_client.get_comments(
            agent_id,
            &creds.api_key,
            post_id,
        ).await
    }
    
    /// Vote on a post
    pub async fn vote_post(
        &self,
        agent_id: &str,
        post_id: &str,
        vote: &str,
    ) -> MoltbookResult<()> {
        let creds = self.get_credentials(agent_id).await?;
        
        self.api_client.vote_post(
            agent_id,
            &creds.api_key,
            post_id,
            vote,
        ).await
    }
    
    /// Vote on a comment
    pub async fn vote_comment(
        &self,
        agent_id: &str,
        comment_id: &str,
        vote: &str,
    ) -> MoltbookResult<()> {
        let creds = self.get_credentials(agent_id).await?;
        
        self.api_client.vote_comment(
            agent_id,
            &creds.api_key,
            comment_id,
            vote,
        ).await
    }
    
    /// Follow or unfollow a user
    pub async fn follow_user(
        &self,
        agent_id: &str,
        target_username: &str,
        unfollow: bool,
    ) -> MoltbookResult<()> {
        let creds = self.get_credentials(agent_id).await?;
        
        self.api_client.follow_agent(
            agent_id,
            &creds.api_key,
            target_username,
            unfollow,
        ).await
    }
    
    /// Search posts and comments
    pub async fn search(
        &self,
        agent_id: &str,
        query: &str,
        search_type: &str,
        limit: usize,
    ) -> MoltbookResult<MoltbookSearchResults> {
        let creds = self.get_credentials(agent_id).await?;
        
        self.api_client.search(
            agent_id,
            &creds.api_key,
            query,
            search_type,
            limit,
        ).await
    }
    
    /// Get profile (self or another user)
    pub async fn get_profile(
        &self,
        agent_id: &str,
        username: Option<&str>,
    ) -> MoltbookResult<MoltbookProfile> {
        let creds = self.get_credentials(agent_id).await?;
        
        // Check cache for self profile
        if username.is_none() {
            let state = self.get_agent_state(agent_id);
            if let Some(cached) = &state.profile_cache {
                let age = current_time_ms() - cached.fetched_at;
                if age < CACHE_TTL_PROFILE_MS {
                    return Ok(cached.data.clone());
                }
            }
        }
        
        let profile = self.api_client.get_profile(
            agent_id,
            &creds.api_key,
            username,
        ).await?;
        
        // Cache self profile
        if username.is_none() {
            let mut state = self.get_agent_state(agent_id);
            state.profile_cache = Some(CachedData {
                data: profile.clone(),
                fetched_at: current_time_ms(),
            });
            self.update_agent_state(agent_id, state);
        }
        
        Ok(profile)
    }
    
    /// Check rate limit status
    pub fn get_rate_limit_status(&self, agent_id: &str) -> RateLimitState {
        self.get_agent_state(agent_id).rate_limits.clone()
    }
    
    /// Check if agent can post
    pub fn can_post(&self, agent_id: &str) -> bool {
        rate_limiter::can_post(agent_id)
    }
    
    /// Check if agent can comment
    pub fn can_comment(&self, agent_id: &str) -> bool {
        rate_limiter::can_comment(agent_id)
    }
    
    /// Get time until next post is allowed
    pub fn time_until_next_post(&self, agent_id: &str) -> i64 {
        rate_limiter::get_time_until_can_post(agent_id)
    }
}

impl Default for MoltbookService {
    fn default() -> Self {
        Self::new(MoltbookConfig::default())
    }
}

// Helper function for current time
fn current_time_ms() -> i64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_millis() as i64
}
