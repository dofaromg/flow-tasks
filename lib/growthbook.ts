import { GrowthBook } from '@growthbook/growthbook'
import { identify } from './identify'

// Initialize GrowthBook instance
let growthbook: GrowthBook | null = null

export function getGrowthBook(): GrowthBook {
  if (typeof window === 'undefined') {
    // Server-side: return a dummy GrowthBook instance
    return new GrowthBook({
      attributes: {},
      features: {},
    })
  }

  if (!growthbook) {
    growthbook = new GrowthBook({
      apiHost: process.env.NEXT_PUBLIC_GROWTHBOOK_API_HOST || 'https://cdn.growthbook.io',
      clientKey: process.env.NEXT_PUBLIC_GROWTHBOOK_CLIENT_KEY || '',
      enableDevMode: process.env.NODE_ENV === 'development',
      trackingCallback: (experiment, result) => {
        console.log('Experiment Viewed', {
          experimentId: experiment.key,
          variationId: result.key,
        })
      },
    })

    // Set user attributes
    const attributes = identify()
    growthbook.setAttributes(attributes)

    // Load features from GrowthBook API
    growthbook.init({ streaming: true }).catch((error) => {
      console.error('Failed to initialize GrowthBook:', error)
    })
  }

  return growthbook
}

// Feature flag helper functions
export function isFeatureOn(featureKey: string): boolean {
  const gb = getGrowthBook()
  return gb.isOn(featureKey)
}

export function getFeatureValue<T>(featureKey: string, defaultValue: T): T {
  const gb = getGrowthBook()
  return gb.getFeatureValue(featureKey, defaultValue)
}

// Flag definitions
export const FLAGS = {
  SHOW_SUMMER_SALE: 'summer_sale',
  SHOW_FREE_DELIVERY: 'free_delivery',
  PROCEED_TO_CHECKOUT_COLOR: 'proceed_to_checkout',
} as const
