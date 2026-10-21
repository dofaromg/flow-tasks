# iOS SDK Compatibility Notes

The iOS SDK should keep Firebase-like call sites while using FireCore transport internally.

Recommended Swift namespace:

```swift
enum MRLFireCore {}
```

Primary modules:

- `MRLFireCore.Auth`
- `MRLFireCore.Store`
- `MRLFireCore.Vault`
- `MRLFireCore.Live`
- `MRLFireCore.Push`
- `MRLFireCore.Trace`

Signing and authority remain outside the client. The client receives signed origin results; it does not sign authoritative state.
