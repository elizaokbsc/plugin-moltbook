//! Moltbook Plugin for ElizaOS (Rust)
//!
//! Social engagement plugin for AI agents to participate in the Moltbook community.
//!
//! # Features
//! - Post creation and commenting
//! - Community browsing and interaction
//! - Voting and following
//! - Semantic search
//! - Rate limiting and quality gating
//! - Autonomous engagement cycle
//!
//! # Architecture
//! - **lib/**: Core API client, rate limiting, and templates
//! - **actions**: User-triggered actions (post, comment, follow, vote, search)
//! - **service**: Main Moltbook service managing state and coordination
//! - **providers**: Context providers for agent prompts
//! - **types**: Type definitions for Moltbook entities
//! - **constants**: Configuration constants and API endpoints
//! - **error**: Error types and handling
//!
//! # Quick Start
//! ```rust,no_run
//! use elizaos_plugin_moltbook::*;
//!
//! // Initialize service
//! let config = MoltbookConfig::default();
//! let service = MoltbookService::new(config);
//!
//! // Service provides access to all Moltbook functionality
//! ```

#![warn(missing_docs)]
#![allow(clippy::module_inception)]

// Core modules
pub mod constants;
pub mod error;
pub mod types;

// Library modules
pub mod lib;

// Plugin components
pub mod actions;
pub mod providers;
pub mod service;

// Re-exports for convenience
pub use actions::*;
pub use constants::*;
pub use error::*;
pub use lib::*;
pub use providers::*;
pub use service::*;
pub use types::*;

/// Plugin version
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Plugin name
pub const NAME: &str = env!("CARGO_PKG_NAME");

/// Helper function to initialize tracing for the plugin
pub fn init_logging() {
    tracing_subscriber::fmt()
        .with_target(false)
        .with_thread_ids(false)
        .with_level(true)
        .init();
}
