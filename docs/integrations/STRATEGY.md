# SMCC Integration Strategy

## Path Comparison

| Path | Speed | Cost | Compliance | Limitations |
|---|---|---|---|---|
| Path 1: Build native SMCC connectors with official APIs (Meta, LinkedIn, X, etc.) | Medium to slow (highest engineering effort) | Direct platform/API costs only | Best licensing control; no third-party copyleft coupling | Per-platform OAuth complexity, app review delays, fragmented API behavior |
| Path 2: Use Ayrshare as unified backend | Fastest to broad platform coverage | Ayrshare subscription + usage costs | Clean boundary if used via API key; SDK licenses are permissive | Vendor dependency, feature parity gaps vs direct APIs, provider lock-in risk |
| Path 3: Self-host Postiz as separate service and integrate at API layer | Medium (faster than building all features from scratch) | Infra + operations for Postiz service | Safe if API-level separation is maintained; AGPL obligations apply to Postiz service distribution/modifications | Operational overhead, contract mismatch risk, AGPL obligations if Postiz is modified and network-served |

## Path 1 Details: Official API Connectors

- Best long-term control for enterprise/compliance-heavy deployments.
- Requires dedicated work per network:
  - OAuth/app review flow
  - publish API variation handling
  - refresh token lifecycle
  - rate-limit and retry policies
- Recommended when SMCC needs deep, platform-specific capabilities beyond common posting.

## Path 2 Details: Ayrshare Unified Backend

- Fastest way to support many social platforms with one connector contract.
- Ideal for MVP and early customer validation.
- Recommended implementation:
  - Use `AYRSHARE_API_KEY` in backend only.
  - Keep connector behind capability flags.
  - Preserve abstraction so Path 1 connectors can replace Ayrshare later without API breakage.

## Path 3 Details: Postiz as Separate Service

- Useful if we want mature scheduling/team workflows immediately.
- Must keep strict service boundary:
  - SMCC <-> Postiz over API/webhook contracts
  - no Postiz source copy into SMCC codebase unless AGPL decision is explicit
- Choose this path only when Postiz feature depth is required and ops/legal tradeoffs are accepted.

## Recommended Sequence

1. Start with Path 2 (Ayrshare) for rapid multi-platform posting.
2. Parallelize Path 1 for strategic platforms where direct API depth matters.
3. Evaluate Path 3 only if we specifically need Postiz product features and can commit to AGPL-aware architecture.
