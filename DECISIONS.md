# Decisions

- Build original stdlib stored-cookie-scope/1 rather than fork a real jar. This keeps
  declared scope separate from parsing, retention, network delivery and authority.
- Defer SameSite; supplied site/navigation/method/browser rules would need another
  reviewed profile. Origin equality cannot implement it.
- Use synthetic `.test` hosts and already declared paths. No automatic IDNA/PSL/IP
  handling or normalization; unsupported context is explicit.
- Expiry equality inclusive on whole-second supplied time; no system clock/session
  lifetime inference. Known failures coexist with unknown independent context.
- Freeze40 hand-assigned full expected reports before core, plus diagnostic bytes,
  literal finite controls and five semantic mutations. A shared renderer cannot be
  the sole semantic oracle; its hand-authored gate outcomes predate implementation.
- Adapt reviewed owned MIT redirect/range admission/delivery patterns with provenance;
  no upstream code copied and no runtime sibling dependency.
- Publish only this separate project, with immutable action pins/minimum permissions,
  per Jake's explicit public-repository instruction. Parent project untouched.
