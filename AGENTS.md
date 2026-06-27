# Repository Rules

## Fork Role

- This fork is the source of truth for OpenBB provider behavior used by `quant-warehouse`.
- Vendor endpoint coverage, pagination, provider schemas, and provider-specific normalization should be fixed here before changing downstream repos.
- The `develop` branch is the branch consumed by downstream Git dependencies.

## Provider Expectations

- FMP routes used by target engineering must fetch complete symbol-level history by default unless the caller explicitly provides a `limit`.
- ThetaData support belongs in the `openbb-thetadata` provider package under `openbb_platform/providers/thetadata`.
- Downstream repos should not call vendor APIs directly to compensate for missing OpenBB provider behavior.

## Compatibility Policy

- This fork is new and intentionally fast-moving. Do not add backward-compatibility shims for old downstream call paths.
- Prefer one clear provider schema and one clear route contract; update downstream callers when route behavior changes.
- Remove deprecated paths instead of keeping aliases, fallbacks, or duplicate implementations.

## Performance Policy

- Keep provider code async/vectorized where the OpenBB provider architecture supports it.
- Do not add GPU/CUDA logic in provider fetchers. CUDA acceleration belongs in downstream compute layers after provider data is normalized.

## Git Hygiene

- Avoid merging `origin/develop` into `develop` when cleaning fork history. Rebase or reset intentionally, then use `git push --force-with-lease` only when rewriting this personal fork.
- Keep duplicated self-merge commits out of `develop`.
