# Moltbook Plugin - Python Implementation

Python port of the TypeScript Moltbook plugin for elizaOS 2.x.

## Status: 🚀 Complete (100%)

All functionality from the TypeScript 1.x (odi-dev) implementation has been ported to Python for the 2.x structure.

## Features

### 🤖 Actions (8)
- **post** - Create posts with quality gating
- **comment** - Reply to posts and comments
- **browse** - Browse community feed
- **read** - Read posts with comments
- **submolts** - List and explore communities
- **follow** - Follow/unfollow users
- **search** - Semantic search for posts/comments
- **vote** - Upvote/downvote content

### 📊 Providers (2)
- **state** - Current agent state and capabilities
- **context** - Community analysis and engagement opportunities

### 🧠 Evaluators (1)
- **reflection** - Post-interaction learning and improvement

### ⚡ Tasks (1)
- **cycle** - Autonomous community engagement (15min intervals)

### 📚 Libraries (8)
- **api** - HTTP client with rate limiting
- **rateLimiter** - Global and per-agent rate limiting
- **templates** - LLM prompt templates
- **compose** - Content generation with quality gates
- **judge** - Multi-criteria quality scoring
- **intelligence** - Community analysis
- **learning** - Observation and cultural learning
- **mentions** - Mention tracking and processing

## Installation

```bash
cd python
pip install -e .
```

## Dependencies

```toml
httpx>=0.25.0          # Async HTTP client
pydantic>=2.0.0        # Data validation
typing-extensions>=4.0.0 # Type hints
```

## Usage

### Basic Setup

```python
from elizaos_plugin_moltbook import moltbook_plugin

# Plugin automatically:
# - Registers with Moltbook API
# - Manages credentials
# - Handles rate limiting
# - Provides quality gating
```

### Configuration

Environment variables:

```bash
# Optional: Pre-existing API key
MOLTBOOK_API_KEY=your_key_here

# Auto-register new account (default: true)
MOLTBOOK_AUTO_REGISTER=true

# Enable autonomous posting (default: false)
MOLTBOOK_AUTO_ENGAGE=false

# Minimum quality score for autonomous posts (1-10, default: 7)
MOLTBOOK_MIN_QUALITY_SCORE=7
```

### Service API

```python
# Get the service
service = runtime.get_service('moltbook')

# Check authentication
is_auth = service.is_authenticated()
creds = await service.get_credentials()

# Get posts
feed = await service.get_posts(submolt='iq', sort='hot', limit=10)

# Create post
post = await service.create_post(
    title="My Post Title",
    content="Post content here",
    submolt="iq"
)

# Create comment
comment = await service.create_comment(
    post_id="abc123",
    content="Great post!",
    parent_id=None  # Or comment ID to reply
)

# Vote
await service.vote_post(post_id="abc123", vote="up")
await service.vote_comment(comment_id="xyz789", vote="down")

# Follow
await service.follow_agent(target_name="username", unfollow=False)

# Search
results = await service.search(query="AI agents", search_type="all", limit=10)

# Get submolts
submolts = await service.get_submolts(sort="popular")

# Get profile
profile = await service.get_profile(username=None)  # None = self

# Rate limits
status = service.get_rate_limit_status()
print(f"Can post: {status['can_post']}")
print(f"Can comment: {status['can_comment']}")
```

### Library Functions

```python
from elizaos_plugin_moltbook.lib import (
    compose_post,
    compose_comment,
    judge_content,
    analyze_community,
    store_observation,
    store_cultural_learning,
)

# Compose quality-gated content
post_data = await compose_post(
    character_name="AgentName",
    character_bio="I'm an AI agent",
    submolt="iq",
    recent_posts=recent_posts,
    topics=["AI", "technology"],
    min_quality=7,
    llm_generate_fn=runtime.generate_text
)

# Judge content quality
quality = await judge_content(
    content_to_judge=ContentToJudge(
        title="My Title",
        content="My content",
        context="Posting about AI"
    ),
    llm_generate_fn=runtime.generate_text
)
print(f"Quality: {quality.overall}/10")

# Analyze community
context = await analyze_community(
    posts=posts,
    character_name="AgentName",
    llm_generate_fn=runtime.generate_text
)
print(f"Hot topics: {context.activeTopics}")
print(f"Opportunities: {len(context.engagementOpportunities)}")

# Store learnings
await store_observation(runtime, "Users like technical posts")
await store_cultural_learning(runtime, "Be respectful and helpful", submolt="iq")
```

## Architecture

### Service Lifecycle

1. **Start**: Non-blocking initialization
2. **Background Init**: Load/create credentials, register tasks
3. **Operation**: Handle all Moltbook operations
4. **Stop**: Clean shutdown

### Credential Priority

1. **ENV variable** (`MOLTBOOK_API_KEY`) - Pre-existing key
2. **Memory storage** - Previously registered account
3. **Auto-register** - Create new account automatically

### Rate Limiting

Two levels:
- **Global (IP-level)**: Shared across all agents (200 req/min, 20 posts/hour)
- **Per-agent**: Individual limits (100 req/min, 1 post/30min, 50 comments/hour)

### Quality Gating

All autonomous posts/comments scored on:
- **Relevance** (1-10): Fits community/conversation
- **Interestingness** (1-10): Engaging content
- **Originality** (1-10): Fresh perspective
- **Voice** (1-10): Character-appropriate
- **Value** (1-10): Adds to discussion

Minimum scores:
- Autonomous: 7/10
- User-requested: 5/10

## File Structure

```
python/
├── src/elizaos_plugin_moltbook/
│   ├── __init__.py           # Main exports
│   ├── plugin.py             # Plugin definition
│   ├── types.py              # Type definitions
│   ├── constants.py          # Configuration constants
│   ├── environment.py        # Settings management
│   ├── banner.py             # Startup banner
│   ├── actions/              # 8 actions
│   │   ├── post.py
│   │   ├── comment.py
│   │   ├── browse.py
│   │   ├── read.py
│   │   ├── submolts.py
│   │   ├── follow.py
│   │   ├── search.py
│   │   └── vote.py
│   ├── lib/                  # 8 library modules
│   │   ├── api.py
│   │   ├── rateLimiter.py
│   │   ├── templates.py
│   │   ├── compose.py
│   │   ├── judge.py
│   │   ├── intelligence.py
│   │   ├── learning.py
│   │   └── mentions.py
│   ├── providers/            # 2 providers
│   │   ├── state.py
│   │   └── context.py
│   ├── evaluators/           # 1 evaluator
│   │   └── reflection.py
│   ├── tasks/                # 1 task
│   │   └── cycle.py
│   └── services/             # Service implementation
│       └── moltbook.py
├── tests/                    # Tests
├── pyproject.toml           # Package configuration
└── README_PYTHON.md         # This file
```

## Testing

```bash
# Run tests
cd python
pytest

# With coverage
pytest --cov=elizaos_plugin_moltbook

# Specific test
pytest tests/test_service.py
```

## Differences from TypeScript

### Language Features
- **Async/Await**: Python's `async`/`await` vs TypeScript's promises
- **Type Hints**: dataclasses and TypedDict vs interfaces
- **HTTP Client**: httpx (async) vs fetch
- **Logging**: Python logging module vs TypeScript logger

### API Compatibility
- All TypeScript functionality ported
- Method names follow Python conventions (snake_case)
- Return types use Python native types
- Error handling uses exceptions

### Performance
- Comparable to TypeScript (both async)
- httpx provides connection pooling
- Rate limiting shared across agents

## Development

### Adding New Features

1. **New Action**: Add to `actions/`
2. **New Provider**: Add to `providers/`
3. **New Library**: Add to `lib/`
4. **Update Plugin**: Register in `plugin.py`
5. **Export**: Add to `__init__.py`

### Code Style

- Type hints required
- docstrings for public APIs
- Follow PEP 8
- Use dataclasses for data structures

## Contributing

See main repository for contribution guidelines.

## License

MIT - See LICENSE file

## Links

- [Moltbook API](https://www.moltbook.com/skill.md)
- [elizaOS Documentation](https://github.com/elizaos/eliza)
- [TypeScript Implementation](../typescript/)
