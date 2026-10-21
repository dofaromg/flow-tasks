import type { Attributes } from '@flags-sdk/growthbook'
import { getStableId } from './get-stable-id'

/**
 * Identify function for GrowthBook
 * Returns user attributes used for feature flag targeting
 */
export function identify(): Attributes {
  const stableId = getStableId()
  
  return {
    id: stableId,
    // Add additional user attributes here as needed
    // For example:
    // email: user?.email,
    // company: user?.company,
    // country: user?.country,
  }
}
