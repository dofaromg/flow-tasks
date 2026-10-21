import { nanoid } from 'nanoid'

/**
 * Reads the stable id from localStorage or returns a new stable id
 * This is a client-side only implementation for Pages Router
 */
export function getStableId(): string {
  if (typeof window === 'undefined') {
    // Server-side: return a temporary ID
    return 'server-temp-id'
  }

  try {
    const stableId = localStorage.getItem('stable-id')
    if (stableId) {
      return stableId
    }
    
    // Generate new stable ID
    const newStableId = nanoid()
    localStorage.setItem('stable-id', newStableId)
    return newStableId
  } catch (error) {
    // Fallback if localStorage is not available
    return nanoid()
  }
}

/**
 * Reset the stable ID (useful for testing different variations)
 */
export function resetStableId(): void {
  if (typeof window !== 'undefined') {
    try {
      localStorage.removeItem('stable-id')
    } catch (error) {
      console.error('Failed to reset stable ID:', error)
    }
  }
}
