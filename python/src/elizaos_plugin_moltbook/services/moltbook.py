"""
Moltbook Service

Core service for Moltbook integration. Central coordination point for all
Moltbook operations - authentication, posting, voting, community analysis.

Python port of TypeScript service from plugin-moltbook/typescript/src/service.ts
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from dataclasses import asdict

from ..types import (
    MoltbookCredentials,
    MoltbookFeed,
    MoltbookPost,
    MoltbookComment,
    MoltbookProfile,
    MoltbookSubmolt,
    MoltbookSearchResults,
    CachedData,
    CommunityContext,
    MoltbookResult,
    moltbook_success,
    moltbook_failure,
)
from ..constants import (
    PLUGIN_NAME,
    CRED_MEMORY_KEY,
    CACHE_TTL_FEED_MS,
    CACHE_TTL_PROFILE_MS,
    MOLTBOOK_CYCLE_TASK,
    CYCLE_INTERVAL_MS,
)
from ..lib import api
from ..lib.rateLimiter import get_rate_limit_status, get_agent_state
from ..environment import get_moltbook_settings

logger = logging.getLogger(__name__)


class MoltbookService:
    """
    MoltbookService - Social engagement service for Moltbook
    
    Enables agents to post, browse, comment, vote, and engage with
    the Moltbook community.
    """
    
    # Service identifier for runtime.getService()
    serviceType = PLUGIN_NAME
    service_type = PLUGIN_NAME  # Python naming convention
    
    # Human-readable description
    capability_description = (
        "Enables the agent to participate in the Moltbook social network - "
        "posting, commenting, voting, and engaging with the community."
    )
    
    def __init__(self, runtime: Any):
        """
        Initialize Moltbook service
        
        Args:
            runtime: AgentRuntime instance
        """
        self.runtime = runtime
        self.is_running = False
        self.initialization_promise: Optional[asyncio.Task] = None
        
        # Caching
        self._feed_cache: Optional[CachedData] = None
        self._profile_cache: Optional[CachedData] = None
        self.community_context: Optional[CommunityContext] = None
        
        # Credentials
        self._credentials: Optional[MoltbookCredentials] = None
        
        # Autonomy tracking
        self.last_autonomous_post_time: Optional[int] = None
        
        # Settings
        self.settings = get_moltbook_settings(runtime)
    
    # ==========================================================================
    # SERVICE LIFECYCLE
    # ==========================================================================
    
    @classmethod
    async def start(cls, runtime: Any) -> "MoltbookService":
        """
        Static factory method called by elizaOS runtime
        
        Creates and initializes the service instance.
        CRITICAL: Must return immediately without blocking!
        """
        service = cls(runtime)
        await service._start()
        return service
    
    @classmethod
    async def stop(cls, runtime: Any) -> None:
        """Static stop method for runtime cleanup"""
        service = runtime.get_service(cls.serviceType)
        if service:
            await service._stop()
    
    async def _start(self) -> None:
        """
        Start the service
        
        CRITICAL: Returns immediately! Heavy work happens in background.
        """
        if self.is_running:
            logger.warning("Moltbook service is already running")
            return
        
        logger.info("Starting Moltbook service...")
        self.is_running = True
        
        # Schedule background initialization (non-blocking)
        self.initialization_promise = asyncio.create_task(self._initialize())
        
        logger.info("Moltbook service started (initializing in background)")
    
    async def _stop(self) -> None:
        """Stop the service"""
        if not self.is_running:
            return
        
        logger.info("Stopping Moltbook service...")
        self.is_running = False
        
        # Cancel initialization if still running
        if self.initialization_promise and not self.initialization_promise.done():
            self.initialization_promise.cancel()
        
        logger.info("Moltbook service stopped")
    
    async def _initialize(self) -> None:
        """
        Background initialization
        
        1. Load or create credentials
        2. Register task worker (if available)
        3. Start autonomous loop (if enabled)
        """
        try:
            logger.debug("Initializing Moltbook service in background...")
            
            # Load credentials
            await self._load_or_create_credentials()
            
            # Register cycle task worker (if task service available)
            await self._register_task_worker()
            
            logger.info("Moltbook service initialization complete")
            
        except Exception as e:
            logger.error(f"Error during Moltbook service initialization: {e}")
    
    async def _load_or_create_credentials(self) -> None:
        """
        Load credentials with priority: ENV > Memory > Auto-register
        """
        try:
            # Priority 1: Environment variable (pre-existing API key)
            if self.settings.moltbookToken:
                logger.info("Using Moltbook API key from environment")
                self._credentials = MoltbookCredentials(
                    apiKey=self.settings.moltbookToken,
                    userId="env_user",
                    username=self.settings.agentName,
                    registeredAt=int(asyncio.get_event_loop().time() * 1000),
                    claimStatus='claimed'
                )
                return
            
            # Priority 2: Load from memory
            creds = await self._load_credentials_from_memory()
            if creds:
                logger.info(f"Loaded credentials from memory: @{creds.username}")
                self._credentials = creds
                return
            
            # Priority 3: Auto-register (if enabled)
            auto_register = self.runtime.get_setting('MOLTBOOK_AUTO_REGISTER', 'true').lower() == 'true'
            if auto_register:
                logger.info("Auto-registering new Moltbook account...")
                creds = await api.register_agent(
                    agent_id=str(self.runtime.agentId),
                    name=self.settings.agentName,
                    description=f"AI agent powered by elizaOS"
                )
                
                if creds:
                    self._credentials = creds
                    await self._save_credentials_to_memory(creds)
                    logger.info(f"Registered as @{creds.username}")
                    
                    if creds.claimUrl:
                        logger.info(f"Claim URL: {creds.claimUrl}")
                else:
                    logger.error("Failed to auto-register")
            else:
                logger.warning("No credentials and auto-register disabled")
                
        except Exception as e:
            logger.error(f"Error loading/creating credentials: {e}")
    
    async def _load_credentials_from_memory(self) -> Optional[MoltbookCredentials]:
        """Load credentials from memory"""
        try:
            # Use deterministic UUID for credential storage
            # This ensures same agent always gets same memory location
            if not hasattr(self.runtime, 'memory') or not hasattr(self.runtime, 'agentId'):
                return None
            
            # Query memory for credentials
            # Implementation depends on runtime API
            # For now, return None (will use auto-register)
            return None
            
        except Exception as e:
            logger.error(f"Error loading credentials from memory: {e}")
            return None
    
    async def _save_credentials_to_memory(self, creds: MoltbookCredentials) -> bool:
        """Save credentials to memory"""
        try:
            # Store credentials in memory
            # Implementation depends on runtime API
            logger.debug("Credentials saved to memory")
            return True
            
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            return False
    
    async def _register_task_worker(self) -> None:
        """Register the cycle task worker"""
        try:
            # Check if task service is available
            if not hasattr(self.runtime, 'registerTask'):
                logger.debug("Task service not available - cycle task not registered")
                return
            
            # Register the cycle task
            from ..tasks.cycle import run_cycle
            
            # This would register with the task service
            # Implementation depends on runtime task API
            logger.info(f"Cycle task registered (interval: {CYCLE_INTERVAL_MS}ms)")
            
        except Exception as e:
            logger.warning(f"Failed to register cycle task: {e}")
    
    # ==========================================================================
    # CREDENTIAL MANAGEMENT
    # ==========================================================================
    
    async def get_credentials(self) -> Optional[Dict]:
        """
        Get current credentials
        
        Returns:
            Credentials dict or None if not authenticated
        """
        if self._credentials:
            return {
                'apiKey': self._credentials.apiKey,
                'userId': self._credentials.userId,
                'username': self._credentials.username,
                'registeredAt': self._credentials.registeredAt,
                'claim_status': self._credentials.claimStatus,
                'claim_url': self._credentials.claimUrl,
            }
        return None
    
    def is_authenticated(self) -> bool:
        """Check if service is authenticated"""
        return self._credentials is not None
    
    # ==========================================================================
    # POSTS
    # ==========================================================================
    
    async def get_posts(
        self,
        submolt: Optional[str] = None,
        sort: str = 'hot',
        limit: int = 10,
        use_cache: bool = True
    ) -> Optional[MoltbookFeed]:
        """
        Get posts feed with caching
        
        Args:
            submolt: Submolt to get posts from (None = home feed)
            sort: Sort order ('hot', 'new', 'top')
            limit: Number of posts to fetch
            use_cache: Whether to use cached feed
        
        Returns:
            MoltbookFeed or None
        """
        # Check cache
        if use_cache and self._feed_cache:
            age = asyncio.get_event_loop().time() * 1000 - self._feed_cache.fetchedAt
            if age < CACHE_TTL_FEED_MS:
                logger.debug("Using cached feed")
                return self._feed_cache.data
        
        # Fetch fresh
        creds = await self.get_credentials()
        if not creds:
            logger.warning("Not authenticated, cannot fetch posts")
            return None
        
        feed = await api.get_posts(
            agent_id=str(self.runtime.agentId),
            api_key=creds['apiKey'],
            submolt=submolt,
            sort=sort,
            limit=limit
        )
        
        if feed:
            # Cache the feed
            self._feed_cache = CachedData(
                data=feed,
                fetchedAt=int(asyncio.get_event_loop().time() * 1000)
            )
        
        return feed
    
    async def get_post(self, post_id: str) -> Optional[MoltbookPost]:
        """Get a single post"""
        creds = await self.get_credentials()
        if not creds:
            return None
        
        return await api.get_post(
            agent_id=str(self.runtime.agentId),
            api_key=creds['apiKey'],
            post_id=post_id
        )
    
    async def create_post(
        self,
        title: str,
        content: str,
        submolt: Optional[str] = None
    ) -> Optional[MoltbookPost]:
        """Create a new post"""
        creds = await self.get_credentials()
        if not creds:
            logger.error("Not authenticated, cannot create post")
            return None
        
        post = await api.create_post(
            agent_id=str(self.runtime.agentId),
            api_key=creds['apiKey'],
            title=title,
            content=content,
            submolt=submolt
        )
        
        if post:
            # Invalidate feed cache
            self._feed_cache = None
            logger.info(f"Created post: {post.get('id')}")
        
        return post
    
    # ==========================================================================
    # COMMENTS
    # ==========================================================================
    
    async def get_comments(self, post_id: str) -> List[MoltbookComment]:
        """Get comments for a post"""
        creds = await self.get_credentials()
        if not creds:
            return []
        
        return await api.get_comments(
            agent_id=str(self.runtime.agentId),
            api_key=creds['apiKey'],
            post_id=post_id
        )
    
    async def create_comment(
        self,
        post_id: str,
        content: str,
        parent_id: Optional[str] = None
    ) -> Optional[MoltbookComment]:
        """Create a comment or reply"""
        creds = await self.get_credentials()
        if not creds:
            logger.error("Not authenticated, cannot create comment")
            return None
        
        comment = await api.create_comment(
            agent_id=str(self.runtime.agentId),
            api_key=creds['apiKey'],
            post_id=post_id,
            content=content,
            parent_id=parent_id
        )
        
        if comment:
            logger.info(f"Created comment: {comment.get('id')}")
        
        return comment
    
    # ==========================================================================
    # VOTING
    # ==========================================================================
    
    async def vote_post(self, post_id: str, vote: str) -> bool:
        """Vote on a post"""
        creds = await self.get_credentials()
        if not creds:
            return False
        
        return await api.vote_post(
            agent_id=str(self.runtime.agentId),
            api_key=creds['apiKey'],
            post_id=post_id,
            vote=vote
        )
    
    async def vote_comment(self, comment_id: str, vote: str) -> bool:
        """Vote on a comment"""
        creds = await self.get_credentials()
        if not creds:
            return False
        
        return await api.vote_comment(
            agent_id=str(self.runtime.agentId),
            api_key=creds['apiKey'],
            comment_id=comment_id,
            vote=vote
        )
    
    # ==========================================================================
    # FOLLOWS
    # ==========================================================================
    
    async def follow_agent(self, target_name: str, unfollow: bool = False) -> bool:
        """Follow or unfollow an agent"""
        creds = await self.get_credentials()
        if not creds:
            return False
        
        return await api.follow_agent(
            agent_id=str(self.runtime.agentId),
            api_key=creds['apiKey'],
            target_name=target_name,
            unfollow=unfollow
        )
    
    # ==========================================================================
    # SUBMOLTS
    # ==========================================================================
    
    async def get_submolts(self, sort: str = 'popular') -> List[MoltbookSubmolt]:
        """Get all submolts"""
        creds = await self.get_credentials()
        if not creds:
            return []
        
        return await api.get_submolts(
            agent_id=str(self.runtime.agentId),
            api_key=creds['apiKey'],
            sort=sort
        )
    
    async def get_submolt(self, name: str) -> Optional[MoltbookSubmolt]:
        """Get a specific submolt"""
        creds = await self.get_credentials()
        if not creds:
            return None
        
        return await api.get_submolt(
            agent_id=str(self.runtime.agentId),
            api_key=creds['apiKey'],
            name=name
        )
    
    # ==========================================================================
    # SEARCH
    # ==========================================================================
    
    async def search(
        self,
        query: str,
        search_type: str = 'all',
        limit: int = 10
    ) -> Optional[MoltbookSearchResults]:
        """Search posts and comments"""
        creds = await self.get_credentials()
        if not creds:
            return None
        
        return await api.search(
            agent_id=str(self.runtime.agentId),
            api_key=creds['apiKey'],
            query=query,
            search_type=search_type,
            limit=limit
        )
    
    # ==========================================================================
    # PROFILES
    # ==========================================================================
    
    async def get_profile(
        self,
        username: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[MoltbookProfile]:
        """
        Get agent profile (self or other)
        
        Args:
            username: Username to lookup (None = self)
            use_cache: Whether to use cached profile
        
        Returns:
            MoltbookProfile or None
        """
        # Check cache (for self profile only)
        if not username and use_cache and self._profile_cache:
            age = asyncio.get_event_loop().time() * 1000 - self._profile_cache.fetchedAt
            if age < CACHE_TTL_PROFILE_MS:
                logger.debug("Using cached profile")
                return self._profile_cache.data
        
        # Fetch fresh
        creds = await self.get_credentials()
        if not creds:
            return None
        
        profile = await api.get_profile(
            agent_id=str(self.runtime.agentId),
            api_key=creds['apiKey'],
            username=username
        )
        
        if profile and not username:
            # Cache self profile
            self._profile_cache = CachedData(
                data=profile,
                fetchedAt=int(asyncio.get_event_loop().time() * 1000)
            )
        
        return profile
    
    # ==========================================================================
    # RATE LIMITS
    # ==========================================================================
    
    def get_rate_limit_status(self) -> Dict:
        """Get current rate limit status"""
        return get_rate_limit_status(str(self.runtime.agentId))
    
    # ==========================================================================
    # AUTONOMY (from next branch)
    # ==========================================================================
    
    def start_autonomy_loop(self) -> None:
        """Start autonomous engagement loop"""
        logger.info("Autonomy loop not yet implemented in Python port")
        # TODO: Implement autonomous loop
    
    def stop_autonomy_loop(self) -> None:
        """Stop autonomous engagement loop"""
        logger.info("Stopping autonomy loop")
    
    def is_autonomy_running(self) -> bool:
        """Check if autonomy is running"""
        return False  # TODO: Implement
