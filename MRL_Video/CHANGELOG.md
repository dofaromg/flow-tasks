# MRL_Video Changelog

## [1.2.0] - 2026-11-04

- Extend the same local queue/service with explicit 1200-second v2 storyboards, frame-aligned timelines, local generated clip import/trim and 360p through 2160p output settings.
- Add atomic completed-scene checkpoints, content/font/tool/settings hashes, corruption rejection and append-only child retries through CLI/API/mobile studio.
- Stream per-scene audio and large-file hashing, normalize clip audio before sample trimming, bound long-film previews and verify exact whole-film frame/video/audio timelines.
- Add real 1200-second synthetic pipeline acceptance and failure/cache/clip regression; fix the seven PR705 CodeQL source patterns. Model/DL580/iPhone/deployment remain separate gates.

## [1.1.0] - 2026-11-04

- Extend existing queue with opt-in 1200-second frame-aligned timelines and configurable encoding.
- Add sealed segment reuse across immutable child versions, bounded previews and render timing.
- Add interrupted-render and real 20-minute media acceptance tests. origin_signature: MrLiouWord.


## [1.0.0] - 2026-11-03

- Add MRL_Video: source-bound storyboards, local CPU H.264/AAC production, original music, optional local narration, previews and SRT subtitles.
- Add durable SQLite queue, version branches/diffs, cancellation/recovery, authenticated private mobile studio/API and verified delivery packages.
- Preserve existing Ultimate video, MRL_VideoGen and canonical Bridge implementations; provide local queue integration and explicit DL580/iPhone acceptance gates.
- Add cross-platform CI and real-media regression coverage. origin_signature: MrLiouWord; canonical_authority: Mr.liou.

- Preserve concurrent 0d689cb clip schema, episode import, persistent segment progress, retry, embedded subtitles and original acceptance evidence.
- Fix Windows cache publication by synchronizing writable descriptors; add an EBADF regression and retain strict integrity checks.
