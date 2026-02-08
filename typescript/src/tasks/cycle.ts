/**
 * Moltbook Cycle Task
 *
 * Periodic task that runs the agent's Moltbook engagement loop.
 *
 * ## WHY A CYCLE TASK?
 *
 * Moltbook doesn't have webhooks, so we need to poll. This task:
 * 1. **Observes** - Fetches feed, learns about community
 * 2. **Listens** - Polls for mentions/replies on our posts
 * 3. **Engages** - Optionally posts/comments (if claimed & enabled)
 * 4. **Reflects** - Stores learnings for future reference
 *
 * ## CYCLE PHASES
 *
 * Each cycle goes through phases in order:
 * 1. Claim status check (can we engage?)
 * 2. Feed fetch & analysis (observation)
 * 3. Mention/reply polling (listening)
 * 4. Cultural reflection (learning)
 * 5. Engagement decision (action)
 */

import type { IAgentRuntime, TaskWorker } from '@elizaos/core';
import { MoltbookService } from '../service';
import { analyzeCommunity, isAnalysisFresh } from '../lib/intelligence';
import { composePost, composeComment } from '../lib/compose';
import { PLUGIN_NAME, MOLTBOOK_CYCLE_TASK, MIN_AUTONOMOUS_POST_INTERVAL_MS } from '../constants';
import type { CommunityContext, EngagementOpportunity, MoltbookPost } from '../types';
import { getAgentState } from '../lib/rateLimiter';
import {
  pollForMentions,
  processMentions,
  recordMyPost,
} from '../lib/mentions';
import {
  reflectOnObservations,
  getLearningsSummary,
} from '../lib/learning';

// Track last autonomous post time per agent
const lastAutonomousPost = new Map<string, number>();

// Track last mention poll time per agent (don't poll too often)
const lastMentionPoll = new Map<string, number>();
const MENTION_POLL_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes between mention polls

/**
 * Moltbook Cycle Task Worker
 *
 * Runs periodically to:
 * 1. Refresh community context
 * 2. Check for engagement opportunities
 * 3. Optionally make autonomous posts
 */
export const moltbookCycleWorker: TaskWorker = {
  name: MOLTBOOK_CYCLE_TASK,

  validate: async (runtime: IAgentRuntime): Promise<boolean> => {
    // Always valid if service exists
    const service = runtime.getService<MoltbookService>(PLUGIN_NAME);
    return !!service;
  },

  execute: async (runtime: IAgentRuntime): Promise<void> => {
    const service = runtime.getService<MoltbookService>(PLUGIN_NAME);
    if (!service) {
      runtime.logger.debug('Moltbook service not available, skipping cycle');
      return;
    }

    // Check if authenticated
    const creds = await service.getCredentials();
    if (!creds) {
      runtime.logger.debug('Moltbook not authenticated, skipping cycle');
      return;
    }

    runtime.logger.debug('Running Moltbook cycle');

    try {
      // =======================================================================
      // PHASE 1: Check claim status
      // =======================================================================
      const status = service.getStatus();
      const canEngage = status.claimed;

      if (!canEngage) {
        // Try to refresh claim status (human might have claimed since last check)
        const nowClaimed = await service.refreshClaimStatus();

        if (!nowClaimed) {
          // Still unclaimed - can observe but not engage
          runtime.logger.debug(
            { claimUrl: status.claimUrl },
            'Moltbook: Account not claimed yet - observing only'
          );

          // Still fetch feed for observation/learning (read-only is allowed)
          await runObservationPhase(runtime, service);

          // Log claim reminder periodically (every cycle while unclaimed)
          if (status.claimUrl) {
            runtime.logger.info(
              { claimUrl: status.claimUrl },
              'Moltbook: Waiting for human to claim account before engaging'
            );
          }
          return;
        }
        // If we get here, account was just claimed! Continue to engagement
        runtime.logger.info('Moltbook: Account claimed! Starting engagement.');
      }

      // =======================================================================
      // PHASE 2: Observation - Fetch feed and analyze community
      // =======================================================================
      const { feed, context } = await runObservationPhase(runtime, service);
      if (!feed || !context) {
        return;
      }

      // =======================================================================
      // PHASE 3: Listening - Poll for mentions and replies on our posts
      // =======================================================================
      await runListeningPhase(runtime, service);

      // =======================================================================
      // PHASE 4: Reflection - Learn from observations
      // =======================================================================
      await runReflectionPhase(runtime, context, feed);

      // =======================================================================
      // PHASE 5: Engagement - Optionally take action
      // =======================================================================
      const autoEngage = runtime.getSetting('MOLTBOOK_AUTO_ENGAGE') === 'true';
      if (!autoEngage) {
        runtime.logger.debug('Auto-engage disabled, cycle complete');
        return;
      }

      const action = await decideAction(runtime, context, service);
      if (!action) {
        runtime.logger.debug('No action decided for this cycle');
        return;
      }

      await executeAction(runtime, action, context, service);
    } catch (error) {
      runtime.logger.error({ error }, 'Error in Moltbook cycle');
    }
  },
};

// =============================================================================
// CYCLE PHASES
// =============================================================================

/**
 * PHASE 2: Observation - Fetch feed and analyze community
 *
 * WHY OBSERVE FIRST?
 * We need to understand the current state of Moltbook before
 * deciding what to do. This gives us context for engagement decisions.
 */
async function runObservationPhase(
  runtime: IAgentRuntime,
  service: MoltbookService
): Promise<{ feed: { posts: MoltbookPost[] } | null; context: CommunityContext | null }> {
  const feed = await service.getFeed({ forceFresh: true });
  if (!feed || feed.posts.length === 0) {
    runtime.logger.debug('No posts in Moltbook feed');
    return { feed: null, context: null };
  }

  const context = analyzeCommunity(feed, runtime);
  runtime.logger.debug(
    { topics: context.activeTopics.slice(0, 3), vibe: context.vibe },
    'Moltbook community context updated'
  );

  return { feed, context };
}

/**
 * PHASE 3: Listening - Poll for mentions and replies
 *
 * WHY POLL FOR MENTIONS?
 * Moltbook doesn't push notifications to us. We need to actively
 * check if anyone has replied to our posts or mentioned us.
 * This enables conversational engagement.
 */
async function runListeningPhase(
  runtime: IAgentRuntime,
  service: MoltbookService
): Promise<void> {
  // Rate limit mention polling to avoid excessive API calls
  const lastPoll = lastMentionPoll.get(runtime.agentId) || 0;
  const timeSinceLastPoll = Date.now() - lastPoll;

  if (timeSinceLastPoll < MENTION_POLL_INTERVAL_MS) {
    runtime.logger.debug(
      { nextPollIn: Math.round((MENTION_POLL_INTERVAL_MS - timeSinceLastPoll) / 1000) },
      'Moltbook: Skipping mention poll (too soon)'
    );
    return;
  }

  try {
    // Poll for new mentions/replies
    const mentions = await pollForMentions(runtime, service);

    if (mentions.length > 0) {
      runtime.logger.info(
        { count: mentions.length },
        'Moltbook: Found new mentions/replies to process'
      );

      // Process them through the message handling pipeline
      const processed = await processMentions(runtime, service, mentions);

      runtime.logger.info(
        { processed, total: mentions.length },
        'Moltbook: Processed mentions/replies'
      );
    }

    lastMentionPoll.set(runtime.agentId, Date.now());
  } catch (error) {
    runtime.logger.warn({ error }, 'Moltbook: Error polling for mentions');
  }
}

/**
 * PHASE 4: Reflection - Learn from observations
 *
 * WHY REFLECT?
 * Without reflection, the agent never improves. By storing
 * observations and extracting learnings, we build up knowledge
 * that improves future engagement quality.
 */
async function runReflectionPhase(
  runtime: IAgentRuntime,
  context: CommunityContext,
  feed: { posts: MoltbookPost[] }
): Promise<void> {
  try {
    await reflectOnObservations(runtime, context, feed);
    runtime.logger.debug('Moltbook: Reflection phase complete');
  } catch (error) {
    runtime.logger.warn({ error }, 'Moltbook: Error in reflection phase');
  }
}

// =============================================================================
// ACTION DECISION
// =============================================================================

/**
 * Action decision types
 */
type ActionDecision =
  | { type: 'post'; topic?: string }
  | { type: 'comment'; opportunity: EngagementOpportunity }
  | { type: 'upvote'; post: MoltbookPost }
  | { type: 'follow'; userId: string }
  | { type: 'observe' };

/**
 * Decide what action to take this cycle
 */
async function decideAction(
  runtime: IAgentRuntime,
  context: CommunityContext,
  service: MoltbookService
): Promise<ActionDecision | null> {
  // Check rate limits
  const status = service.getStatus();

  // Priority 1: High-priority engagement opportunities
  const highPriorityOpps = context.engagementOpportunities.filter(
    (o) => o.priority >= 8 && o.type === 'comment'
  );

  if (highPriorityOpps.length > 0 && status.rateLimits.canComment) {
    // 60% chance to engage with high-priority opportunity
    if (Math.random() < 0.6) {
      return { type: 'comment', opportunity: highPriorityOpps[0] };
    }
  }

  // Priority 2: Consider autonomous posting
  const lastPost = lastAutonomousPost.get(runtime.agentId) || 0;
  const timeSinceLastPost = Date.now() - lastPost;

  if (status.rateLimits.canPost && timeSinceLastPost >= MIN_AUTONOMOUS_POST_INTERVAL_MS) {
    // 30% chance to post if conditions are right
    if (Math.random() < 0.3) {
      // Pick a topic from active topics or character interests
      const topic = pickTopic(runtime, context);
      return { type: 'post', topic };
    }
  }

  // Priority 3: Medium-priority engagement
  const mediumPriorityOpps = context.engagementOpportunities.filter(
    (o) => o.priority >= 5 && o.priority < 8
  );

  if (mediumPriorityOpps.length > 0 && status.rateLimits.canComment) {
    // 25% chance to engage
    if (Math.random() < 0.25) {
      return { type: 'comment', opportunity: mediumPriorityOpps[0] };
    }
  }

  // Priority 4: Upvote good content
  const upvoteOpps = context.engagementOpportunities.filter((o) => o.type === 'upvote');

  if (upvoteOpps.length > 0 && status.rateLimits.canRequest) {
    // 40% chance to upvote
    if (Math.random() < 0.4) {
      return { type: 'upvote', post: upvoteOpps[0].post };
    }
  }

  // Priority 5: Follow interesting users
  const followOpps = context.engagementOpportunities.filter((o) => o.type === 'follow');

  if (followOpps.length > 0 && status.rateLimits.canRequest) {
    // 20% chance to follow
    if (Math.random() < 0.2) {
      return { type: 'follow', userId: followOpps[0].post.authorId };
    }
  }

  // Default: Just observe
  return { type: 'observe' };
}

/**
 * Pick a topic for autonomous posting
 */
function pickTopic(runtime: IAgentRuntime, context: CommunityContext): string | undefined {
  // 50% chance to use active topic, 50% chance to use character topic
  if (Math.random() < 0.5 && context.activeTopics.length > 0) {
    return context.activeTopics[
      Math.floor(Math.random() * Math.min(3, context.activeTopics.length))
    ];
  }

  // Use character topics if available
  if (runtime.character.topics && runtime.character.topics.length > 0) {
    return runtime.character.topics[Math.floor(Math.random() * runtime.character.topics.length)];
  }

  return undefined;
}

/**
 * Execute the decided action
 */
async function executeAction(
  runtime: IAgentRuntime,
  action: ActionDecision,
  context: CommunityContext,
  service: MoltbookService
): Promise<void> {
  switch (action.type) {
    case 'post': {
      runtime.logger.info({ topic: action.topic }, 'Composing autonomous Moltbook post');

      const composed = await composePost(runtime, context, action.topic, true);
      if (!composed || !composed.qualityScore.pass) {
        runtime.logger.debug(
          { score: composed?.qualityScore.overall },
          'Autonomous post did not meet quality threshold'
        );
        return;
      }

      const post = await service.createPost(composed.title, composed.content);
      if (post) {
        lastAutonomousPost.set(runtime.agentId, Date.now());
        runtime.logger.info(
          { postId: post.id, title: post.title, score: composed.qualityScore.overall },
          'Created autonomous Moltbook post'
        );

        // Record the post so we can monitor for replies
        await recordMyPost(runtime, post);
      }
      break;
    }

    case 'comment': {
      const { opportunity } = action;
      runtime.logger.info(
        { postId: opportunity.post.id, reason: opportunity.reason },
        'Composing autonomous Moltbook comment'
      );

      // Get existing comments for context
      const existingComments = await service.getComments(opportunity.post.id);
      const commentTexts = existingComments.map((c) => c.content);

      const composed = await composeComment(
        runtime,
        opportunity.post.title,
        opportunity.post.content,
        context,
        commentTexts,
        true
      );

      if (!composed || !composed.qualityScore.pass) {
        runtime.logger.debug(
          { score: composed?.qualityScore.overall },
          'Autonomous comment did not meet quality threshold'
        );
        return;
      }

      const comment = await service.createComment(opportunity.post.id, composed.content);
      if (comment) {
        runtime.logger.info(
          {
            postId: opportunity.post.id,
            commentId: comment.id,
            score: composed.qualityScore.overall,
          },
          'Created autonomous Moltbook comment'
        );
      }
      break;
    }

    case 'upvote': {
      const success = await service.votePost(action.post.id, 'up');
      if (success) {
        runtime.logger.debug({ postId: action.post.id }, 'Upvoted Moltbook post');
      }
      break;
    }

    case 'follow': {
      const success = await service.follow(action.userId);
      if (success) {
        runtime.logger.debug({ userId: action.userId }, 'Followed Moltbook user');
      }
      break;
    }

    case 'observe':
      runtime.logger.debug('Observation cycle - no action taken');
      break;
  }
}

export default moltbookCycleWorker;
