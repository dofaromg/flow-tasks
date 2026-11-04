# MRL_Video Changelog

## [1.0.0] - 2026-11-03

- Add MRL_Video: source-bound storyboards, local CPU H.264/AAC production, original music, optional local narration, previews and SRT subtitles.
- Add durable SQLite queue, version branches/diffs, cancellation/recovery, authenticated private mobile studio/API and verified delivery packages.
- Preserve existing Ultimate video, MRL_VideoGen and canonical Bridge implementations; provide local queue integration and explicit DL580/iPhone acceptance gates.
- Add cross-platform CI and real-media regression coverage. origin_signature: MrLiouWord; canonical_authority: Mr.liou.

## [1.1.0] - 2026-11-04

- Extend existing queue with opt-in 1200-second frame-aligned timelines and configurable encoding.
- Add sealed segment reuse across immutable child versions, bounded previews and render timing.
- Add interrupted-render and real 20-minute media acceptance tests. origin_signature: MrLiouWord.



## 1.1.0 · 2026-11-04

Extend PR #705 with local clip-based 1200-second timelines, persistent segment queue, verified content cache, child-version retry, existing episode import, PCM segment normalization, one final AAC encode, frame-aligned subtitles, bounded previews, fullhd/uhd profiles, streaming package hashes and real synthetic CI acceptance. Preserve original MRL names and origin_signature: MrLiouWord. Fix the seven reported CodeQL code patterns; fresh scan remains required.
