// Moltbook API Client
//
// HTTP client with rate limiting, retry logic, and error handling
//
// Rust port of TypeScript api module

use reqwest::{Client, Response, StatusCode};
use serde::de::DeserializeOwned;
use serde_json::json;
use std::time::Duration;

use crate::constants::*;
use crate::types::*;
use super::rate_limiter;

/// API client for Moltbook
pub struct MoltbookApiClient {
    client: Client,
    base_url: String,
}

impl MoltbookApiClient {
    /// Create a new API client
    pub fn new() -> Self {
        let client = Client::builder()
            .timeout(Duration::from_millis(HTTP_TIMEOUT_MS))
            .user_agent("elizaOS-moltbook-plugin/2.0-rust")
            .build()
            .unwrap();
        
        Self {
            client,
            base_url: MOLTBOOK_API_URL.to_string(),
        }
    }
    
    /// Make a request with retries and rate limiting
    async fn request<T: DeserializeOwned>(
        &self,
        agent_id: &str,
        endpoint: &str,
        method: &str,
        api_key: Option<&str>,
        body: Option<serde_json::Value>,
        skip_rate_limit: bool,
    ) -> MoltbookResult<T> {
        // Check rate limits
        if !skip_rate_limit && !rate_limiter::can_make_request(agent_id) {
            return Err(MoltbookError::RateLimitError(
                "Rate limited - too many requests".to_string()
            ));
        }
        
        let url = format!("{}{}", self.base_url, endpoint);
        let mut request = match method {
            "GET" => self.client.get(&url),
            "POST" => self.client.post(&url),
            "DELETE" => self.client.delete(&url),
            "PUT" => self.client.put(&url),
            "PATCH" => self.client.patch(&url),
            _ => return Err(MoltbookError::ApiError("Invalid HTTP method".to_string())),
        };
        
        // Add headers
        request = request.header("Content-Type", "application/json");
        if let Some(key) = api_key {
            request = request.header("Authorization", format!("Bearer {}", key));
        }
        
        // Add body
        if let Some(body_data) = body {
            request = request.json(&body_data);
        }
        
        // Retry loop
        let mut last_error = None;
        for attempt in 0..HTTP_MAX_RETRIES {
            match request.try_clone().unwrap().send().await {
                Ok(response) => {
                    // Record request
                    if !skip_rate_limit {
                        rate_limiter::record_request(agent_id);
                    }
                    
                    // Handle rate limit
                    if response.status() == StatusCode::TOO_MANY_REQUESTS {
                        if let Some(retry_after) = response.headers().get("retry-after") {
                            if let Ok(seconds) = retry_after.to_str().unwrap_or("60").parse::<i64>() {
                                rate_limiter::set_global_retry_after(seconds);
                            }
                        }
                        return Err(MoltbookError::RateLimitError(
                            "Rate limited by server".to_string()
                        ));
                    }
                    
                    // Handle errors
                    if !response.status().is_success() {
                        let error_text = response.text().await.unwrap_or_default();
                        
                        // Retry on 5xx
                        if response.status().is_server_error() && attempt < HTTP_MAX_RETRIES - 1 {
                            let delay = Duration::from_millis(HTTP_RETRY_BASE_DELAY_MS * 2_u64.pow(attempt as u32));
                            tokio::time::sleep(delay).await;
                            continue;
                        }
                        
                        return Err(MoltbookError::ApiError(format!(
                            "HTTP {}: {}",
                            response.status(),
                            error_text
                        )));
                    }
                    
                    // Parse response
                    match response.json::<T>().await {
                        Ok(data) => return Ok(data),
                        Err(e) => return Err(MoltbookError::SerializationError(e.into())),
                    }
                }
                Err(e) => {
                    last_error = Some(e);
                    if attempt < HTTP_MAX_RETRIES - 1 {
                        let delay = Duration::from_millis(HTTP_RETRY_BASE_DELAY_MS * 2_u64.pow(attempt as u32));
                        tokio::time::sleep(delay).await;
                        continue;
                    }
                }
            }
        }
        
        Err(MoltbookError::NetworkError(last_error.unwrap()))
    }
    
    // =========================================================================
    // AUTHENTICATION
    // =========================================================================
    
    pub async fn register_agent(
        &self,
        agent_id: &str,
        name: &str,
        description: &str,
    ) -> MoltbookResult<MoltbookCredentials> {
        let body = json!({
            "name": name,
            "description": description,
        });
        
        let response: serde_json::Value = self.request(
            agent_id,
            endpoints::REGISTER,
            "POST",
            None,
            Some(body),
            true, // Skip rate limit for registration
        ).await?;
        
        Ok(MoltbookCredentials {
            api_key: response["api_key"].as_str().unwrap_or("").to_string(),
            user_id: response["id"].as_str().unwrap_or("").to_string(),
            username: response["name"].as_str().unwrap_or(name).to_string(),
            registered_at: current_time_ms(),
            claim_status: response["claim_status"].as_str().map(String::from),
            claim_url: response["claim_url"].as_str().map(String::from),
        })
    }
    
    pub async fn get_profile(
        &self,
        agent_id: &str,
        api_key: &str,
        username: Option<&str>,
    ) -> MoltbookResult<MoltbookProfile> {
        let endpoint = if let Some(name) = username {
            endpoints::agent_profile(name)
        } else {
            endpoints::ME.to_string()
        };
        
        self.request(agent_id, &endpoint, "GET", Some(api_key), None, false).await
    }
    
    // =========================================================================
    // POSTS
    // =========================================================================
    
    pub async fn get_posts(
        &self,
        agent_id: &str,
        api_key: &str,
        submolt: Option<&str>,
        sort: &str,
        limit: usize,
    ) -> MoltbookResult<MoltbookFeed> {
        let endpoint = if let Some(sub) = submolt {
            format!("{}/feed?sort={}&limit={}", endpoints::submolt_by_name(sub), sort, limit)
        } else {
            format!("{}?sort={}&limit={}", endpoints::FEED, sort, limit)
        };
        
        self.request(agent_id, &endpoint, "GET", Some(api_key), None, false).await
    }
    
    pub async fn create_post(
        &self,
        agent_id: &str,
        api_key: &str,
        title: &str,
        content: &str,
        submolt: Option<&str>,
    ) -> MoltbookResult<MoltbookPost> {
        if !rate_limiter::can_post(agent_id) {
            return Err(MoltbookError::RateLimitError("Cannot post - rate limited".to_string()));
        }
        
        let mut body = json!({
            "title": title,
            "content": content,
        });
        
        if let Some(sub) = submolt {
            body["submolt"] = json!(sub);
        }
        
        let result = self.request(agent_id, endpoints::POSTS, "POST", Some(api_key), Some(body), false).await;
        
        if result.is_ok() {
            rate_limiter::record_post(agent_id);
        }
        
        result
    }
    
    // =========================================================================
    // COMMENTS
    // =========================================================================
    
    pub async fn get_comments(
        &self,
        agent_id: &str,
        api_key: &str,
        post_id: &str,
    ) -> MoltbookResult<Vec<MoltbookComment>> {
        self.request(
            agent_id,
            &endpoints::comments(post_id),
            "GET",
            Some(api_key),
            None,
            false,
        ).await
    }
    
    pub async fn create_comment(
        &self,
        agent_id: &str,
        api_key: &str,
        post_id: &str,
        content: &str,
        parent_id: Option<&str>,
    ) -> MoltbookResult<MoltbookComment> {
        if !rate_limiter::can_comment(agent_id) {
            return Err(MoltbookError::RateLimitError("Cannot comment - rate limited".to_string()));
        }
        
        let mut body = json!({ "content": content });
        if let Some(parent) = parent_id {
            body["parent_id"] = json!(parent);
        }
        
        let result = self.request(
            agent_id,
            &endpoints::comments(post_id),
            "POST",
            Some(api_key),
            Some(body),
            false,
        ).await;
        
        if result.is_ok() {
            rate_limiter::record_comment(agent_id);
        }
        
        result
    }
    
    // =========================================================================
    // VOTING
    // =========================================================================
    
    pub async fn vote_post(
        &self,
        agent_id: &str,
        api_key: &str,
        post_id: &str,
        vote: &str,
    ) -> MoltbookResult<()> {
        let endpoint = if vote == "up" {
            endpoints::upvote(post_id)
        } else {
            endpoints::downvote(post_id)
        };
        
        let _: serde_json::Value = self.request(agent_id, &endpoint, "POST", Some(api_key), None, false).await?;
        Ok(())
    }
    
    pub async fn vote_comment(
        &self,
        agent_id: &str,
        api_key: &str,
        comment_id: &str,
        vote: &str,
    ) -> MoltbookResult<()> {
        let endpoint = if vote == "up" {
            endpoints::comment_upvote(comment_id)
        } else {
            endpoints::comment_downvote(comment_id)
        };
        
        let _: serde_json::Value = self.request(agent_id, &endpoint, "POST", Some(api_key), None, false).await?;
        Ok(())
    }
    
    // =========================================================================
    // FOLLOWS
    // =========================================================================
    
    pub async fn follow_agent(
        &self,
        agent_id: &str,
        api_key: &str,
        target_name: &str,
        unfollow: bool,
    ) -> MoltbookResult<()> {
        let method = if unfollow { "DELETE" } else { "POST" };
        let _: serde_json::Value = self.request(
            agent_id,
            &endpoints::agent_follow(target_name),
            method,
            Some(api_key),
            None,
            false,
        ).await?;
        Ok(())
    }
    
    // =========================================================================
    // SUBMOLTS
    // =========================================================================
    
    pub async fn get_submolts(
        &self,
        agent_id: &str,
        api_key: &str,
        sort: &str,
    ) -> MoltbookResult<Vec<MoltbookSubmolt>> {
        self.request(
            agent_id,
            &format!("{}?sort={}", endpoints::SUBMOLTS, sort),
            "GET",
            Some(api_key),
            None,
            false,
        ).await
    }
    
    pub async fn get_submolt(
        &self,
        agent_id: &str,
        api_key: &str,
        name: &str,
    ) -> MoltbookResult<MoltbookSubmolt> {
        self.request(
            agent_id,
            &endpoints::submolt_by_name(name),
            "GET",
            Some(api_key),
            None,
            false,
        ).await
    }
    
    // =========================================================================
    // SEARCH
    // =========================================================================
    
    pub async fn search(
        &self,
        agent_id: &str,
        api_key: &str,
        query: &str,
        search_type: &str,
        limit: usize,
    ) -> MoltbookResult<MoltbookSearchResults> {
        let endpoint = format!("{}?q={}&type={}&limit={}", 
            endpoints::SEARCH,
            urlencoding::encode(query),
            search_type,
            limit
        );
        
        self.request(agent_id, &endpoint, "GET", Some(api_key), None, false).await
    }
}

impl Default for MoltbookApiClient {
    fn default() -> Self {
        Self::new()
    }
}
