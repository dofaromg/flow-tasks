# Web SDK Compatibility Notes

The Web SDK surface should preserve Firebase-style ergonomics while routing to FireCore endpoints.

Recommended module shape:

```ts
import { createFireCoreClient } from '@mrl/firecore-web';
const firecore = createFireCoreClient({ baseUrl: 'https://firecore.mrliouword.com' });
```

Mapping:

- `auth().signInWithEmailAndPassword` -> `POST /v1/auth/signin`
- `firestore().doc(path).set` -> `POST /v1/store/documents`
- `storage().ref(key).put` -> `POST /v1/vault/objects`
- `onSnapshot` -> `/v1/live/stream` or `/v1/live/ws`
- `messaging().getToken` -> `POST /v1/push/register`
- `analytics().logEvent` -> `POST /v1/trace/events`
