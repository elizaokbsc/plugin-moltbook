/**
 * Moltbook Plugin for elizaOS
 *
 * Enables AI agents to participate in the Moltbook social network
 * as genuine community members.
 *
 * @packageDocumentation
 */

export { moltbookPlugin, moltbookPlugin as default } from './plugin';
export { MoltbookService } from './service';
export * from './types';
export * from './constants';

// Export evaluators for external use
export { reflectionEvaluator } from './evaluators';

// Export learning utilities for advanced use cases
export {
  storeObservation,
  storeCulturalLearning,
  rememberNotableUser,
  getCulturalLearnings,
  getNotableUsers,
  getRecentObservations,
  getLearningsSummary,
  formatCulturalLearnings,
  formatNotableUsers,
} from './lib/learning';

// Export mention utilities
export {
  pollForMentions,
  processMentions,
  recordMyPost,
  getMyPosts,
  commentToMemory,
} from './lib/mentions';

// Export additional convenience actions from next branch
export {
  moltbookReadAction,
  moltbookSubmoltsAction,
} from './actions';

// Export new provider from next branch
export { moltbookStateProvider } from './providers';

// Export environment utilities from next branch
export { getMoltbookSettings, validateMoltbookSettings } from './environment';
