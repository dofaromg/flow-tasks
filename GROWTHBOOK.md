# GrowthBook Feature Flags Integration

This repository integrates GrowthBook feature flags for A/B testing and feature management.

## Setup

### 1. Install Dependencies

Dependencies are already included in `package.json`. To install:

```bash
npm install
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env.local`:

```bash
cp .env.example .env.local
```

Edit `.env.local` and add your GrowthBook credentials:

```env
NEXT_PUBLIC_GROWTHBOOK_API_HOST=https://cdn.growthbook.io
NEXT_PUBLIC_GROWTHBOOK_CLIENT_KEY=your_actual_client_key
```

You can get your client key from [GrowthBook](https://app.growthbook.io).

### 3. Create Feature Flags in GrowthBook

Log in to your GrowthBook account and create the following feature flags:

1. **summer_sale** (Boolean)
   - Controls the summer sale banner visibility
   - Set up 50% rollout or A/B test

2. **free_delivery** (Boolean)
   - Controls the free delivery banner visibility
   - Set up 50% rollout or A/B test

3. **proceed_to_checkout** (String)
   - Controls the checkout button color
   - Values: `blue`, `green`, or `red`
   - Set up multi-variant test

### 4. Run the Application

```bash
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) to see the feature flags in action.

## How It Works

### Architecture

The GrowthBook integration consists of:

1. **lib/get-stable-id.ts**: Manages user stable ID for consistent feature flag assignment
2. **lib/identify.ts**: Provides user attributes to GrowthBook for targeting
3. **lib/growthbook.ts**: Initializes and manages the GrowthBook SDK
4. **pages/index.js**: Demo page showing feature flags in action

### Feature Flags

The demo includes three feature flags:

- **Summer Sale Banner**: Shows a yellow banner with sale information
- **Free Delivery Banner**: Shows a blue banner with delivery information  
- **Checkout Button Color**: Changes the primary CTA button color

### Testing Different Variations

The application uses a "stable ID" stored in localStorage to ensure users see consistent feature flag variations. To test different variations:

1. Open browser DevTools
2. Go to Application > Local Storage
3. Delete the `stable-id` key
4. Refresh the page

You should see different feature flag variations randomly assigned.

## Development

### Adding New Feature Flags

1. Define the flag in GrowthBook dashboard
2. Add the flag key to `lib/growthbook.ts` in the `FLAGS` constant
3. Use the flag in your component:

```javascript
import { isFeatureOn, getFeatureValue, FLAGS } from '../lib/growthbook';

function MyComponent() {
  const [myFlag, setMyFlag] = useState(false);

  useEffect(() => {
    const gb = getGrowthBook();
    const updateFlags = () => {
      setMyFlag(isFeatureOn(FLAGS.MY_NEW_FLAG));
    };
    updateFlags();
    const unsubscribe = gb.subscribe(updateFlags);
    return () => unsubscribe();
  }, []);

  return myFlag ? <NewFeature /> : <OldFeature />;
}
```

### Flag Types

- **Boolean flags**: Use `isFeatureOn(flagKey)`
- **Value flags**: Use `getFeatureValue(flagKey, defaultValue)`

## Resources

- [GrowthBook Documentation](https://docs.growthbook.io/)
- [GrowthBook React SDK](https://docs.growthbook.io/lib/react)
- [Feature Flags Best Practices](https://docs.growthbook.io/guide/feature-flags-best-practices)

## Troubleshooting

### Flags Not Loading

1. Check that `NEXT_PUBLIC_GROWTHBOOK_CLIENT_KEY` is set correctly
2. Verify the feature flags exist in GrowthBook dashboard
3. Check browser console for errors
4. Ensure GrowthBook API host is accessible

### Inconsistent Flag Values

If you see inconsistent feature flag values, clear the stable ID from localStorage and refresh the page.

### Development Mode

The GrowthBook SDK runs in development mode when `NODE_ENV=development`, which provides additional console logging for debugging.
