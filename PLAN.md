# Approved plan: stored-cookie scope lab

Jake directly approved all four stages with 'okay, push when complete' after this
plan was presented, and explicitly selected public jfrance167/cookie-scoping-policy-lab.
Build, create/push repository and security baseline are now authorized. Supersedes
research-only/pending approval statements below; no merge/deployment authorized.

Tier 3 bounded local portfolio lab. All four stages and public repository creation,
push and the GitHub security baseline are authorized. No merge or deployment.

## Problem and success

Teach the difference between normalized stored-cookie scope checks and actual
browser delivery/authentication. Compare host-only with domain scope, slash-boundary
path behavior, secure transport and supplied-clock expiry. Produce reproducible
conditional results and explicit unknown/excluded contexts with independent checks.

Select ONE profile: `stored-cookie-scope/1`. Original stdlib core/CLI, no API or
dashboard. docs/RESEARCH.md records alternatives/source/license/reuse assessment.

## Exact proposed input contract

Top level contains only `version` (exact integer1) and `cases` (1â€“40 records).
Every case contains exactly `id`, `cookie`, `request`, `unsupported_features`.
ID: unique visible ASCII `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`; denotes a synthetic
test record, never a cookie name. Cookie contains exactly `domain`, `host_only`,
`path`, `secure`, `lifetime`, `expires_at`. Request contains exactly `host`, `path`,
`secure_transport`, `now`. No raw URL, header, cookie value/name or Set-Cookie field.

- Domain/host: exact string or null. Supported names are already lowercase ASCII
  LDH labels, 1â€“63 characters each, no leading/trailing hyphen, length<=253, at least
  two labels, final label `test`; no `xn--` label. `test` alone, uppercase, raw leading
  dot, trailing dot, IP/IDNA/non-test namespace are explicit unsupported context.
  Namespace restriction is synthetic lab policy, not a public-suffix algorithm.
- Cookie/request paths: string or null, length1â€“256, begin `/`, otherwise only
  ASCII letters/digits `/ - . _ ~` (space is NOT in the allowlist). Segment `.` or
  `..` is unsupported. Percent encoding, query, fragment, backslash/non-ASCII/raw
  URI contexts unsupported. Slash/case/duplicate slash preserved; no decoding,
  canonicalization or trimming. Cookie path already includes any earlier default.
- host_only/secure/secure_transport: exact bool or null (unknown). Never infer from
  domain leading dot, scheme, origin or port. Known secure=false does not require
  transport context; secure=true requires true transport to pass.
- lifetime: exact `session`, `persistent`, `unknown`. Session and unknown require
  expires_at=null. Persistent permits exact integer0..9999999999 or null unknown.
  now: exact integer in the same range or null. Persistent comparison needs both;
  session ignores now under explicit still-retained assumption. No system clock.
- unsupported_features: exact list of0â€“8 distinct lowercase ASCII hyphenated
  identifiers, length1â€“32, visible in fixed-order result. Nonempty means unsupported;
  never ignore an unrecognized feature. SameSite, partitioning, public-suffix
  admission, actual browser policies and storage/setting semantics are excluded.

Structural/type/key/count violations are INVALID for the whole document, with fixed
diagnostic code and no partial evaluation. Noncanonical-but-bounded visible strings
are structurally valid but UNSUPPORTED, with fixed reasons; controls/surrogates are
INVALID. Null is missing context, never a wildcard. Full known schema validation
occurs before shortcuts; invalid later cases cannot disappear behind earlier rejects.

Admission bounds for CLI AND public library: exact built-in dict/list/str/int/bool/
None only; type identity before iteration/hash/equality/coercion. Reject subclasses,
custom objects/generators, cycles; aliases may be admitted but counted per occurrence.
No concurrent-mutation guarantee. UTF8 input<=65536 bytes; equivalent compact API
serialization also<=65536; no silent truncation. Max native/JSON container depth8
(top container1), total5000 nodes including keys, per-container100 items,
strings256/key64. JSON numeric tokens<=10 digits excluding minus; finite integer
only, no floats/NaN/Infinity; no duplicate keys. Domain253 and field-specific limits
apply afterward. Semantic time is nonnegative even though walker can inspect negative
bounded integers. Freeze diagnostics/order in stage1 before model.

## Exact semantic and report contract

Independent four gates `domain`, `path`, `transport`, `expiry`, each PASS/FAIL/UNKNOWN
plus fixed ordered reasons. Domain PASS for exact host equality when host_only=true;
otherwise equality OR suffix with preceding dot. Unknown host_only always UNKNOWN;
no cross-origin or same-site calculation. Path PASS on equality OR cookie-path prefix
ending slash OR prefix whose next request character is slash. `/app` fails `/apple`
and passes `/app/x`; `/app/` fails `/app`. Root covers all supported absolute paths.
Transport PASS when secure=false OR secure=true and transport=true; secure=true with
false transport FAIL; secure=null UNKNOWN even when transport=true. Persistent
expiry FAIL when expires_at<=now, otherwise PASS; missing required time UNKNOWN.
Session PASS conditionally on retained stored record; unknown lifetime UNKNOWN.

Evaluate gates independently; don't erase a known domain failure because expiry is
unknown. `scope_decision`: NOT_ELIGIBLE if ANY FAIL; ELIGIBLE_UNDER_ASSUMPTIONS if ALL
PASS; otherwise UNRESOLVED. `profile_status`: UNSUPPORTED if ANY gate UNKNOWN or
unsupported feature/noncanonical context; otherwise SUPPORTED. Unsupported features
prevent ELIGIBLE_UNDER_ASSUMPTIONS: if no FAIL, decision becomes UNRESOLVED even when
all narrower gates PASS. Keep supported-case eligibility separate from profile status.
Wrong-format host/path makes that gate UNKNOWN, never compare a raw unsupported name.

Versioned full report contains profile/version, ordered results (ID, input declarations,
four gates/reasons, unsupported contexts, profile_status, scope_decision), statistics
for all status/decision combinations and fixed assumptions. No values/header selection,
name collision ordering or actual transmission. Preserve null context explicitly.

Assumptions in EACH report: supplied synthetic metadata, already admitted/retained
storage, canonical hosts/paths, declared secure transport, supplied whole-second clock;
browser delivery, session/authentication and storage acceptance are unverified.
Full JSON and inert Markdown output; Markdown entity-escape all caller text, JSON
ensure_ascii, no active link/HTML/terminal-control material. Render entire payload
before delivery; final UTF8 bytes<=524288 for either format. Output cap is application
admission, not proof of process hard memory/time limits. Measure admitted stress and
label any reduced-cap seam honestly; don't invent natural overflow.

CLI statuses:0 all rows SUPPORTED (includes known NOT_ELIGIBLE),2 any UNSUPPORTED,
1 invalid input/output failure. Exact binary LF JSON bytes on Windows; checked writes
accept exact integer byte count only (reject bool/float/None), flush/closed/broken
stream errors fail honestly. Exclusive fresh output, reject input/output alias, remove
only owned failed output when possible, fixed diagnostic if cleanup fails. Trusted
local CLI paths; no hostile filesystem race/durability/atomic stdout claim.

## Architecture, threat model and dependencies

`cookielab/contracts.py` strict admission; `model.py` pure scope gates; `report.py`
bounded rendering/fresh-file delivery; `__main__.py` CLI; tests/tools are separate.
Adapt owned MIT redirect contracts/report/CLI only after full surrounding review;
capture original identities, attribution and focused fixes, no sibling runtime imports.
Stdlib json/re/os/argparse only where needed; no new dependencies/install/upstream
execution. Installed Bandit verifier may be reused after checking availability.

Assets: truthful teaching results, local files/output integrity, bounded resources.
Attacker can craft synthetic JSON/native objects, invalid types, misleading labels,
oversize/deep inputs and conflicting/unknown declarations. Trusted model code and
schemas enforce admission; caller declarations are assumptions, not authenticated
browser/session facts. Fixed diagnostics avoid reflecting rejected content. Threats:
suffix/prefix bugs, expiry equality mistakes, unknown silently allowing, misleading
safe/auth wording, resource growth, callback invocation and output injection/failure.
Mitigations: independent gates, whole validation, native identity, finite limits,
inert output, independent fixtures/mutations and immediate review of boundary code.
Residuals: dishonest context, excluded policies, OS resources/races, actual browser
version behavior and hostile streams; no universal conformance/security verdict.

No cookie setting/admission/default-path computation/PSL or IDNA library; no
SameSite/HttpOnly non-HTTP API/partitioning/privacy/site calculation; no actual cookies,
jars/session/browser storage/headers/credentials/network/services. No imports of
cookiejar/http.cookies/aiohttp/browser clients in app. Tests use only invented metadata.

## Approved stages and definitions of done

1. Freeze contract and oracles: docs/CONTRACT.md, fixtures/cases.json,
   fixtures/expected.json, fixtures/expected.md and fixtures/diagnostics.json. Forty
   independently reasoned full reports cover equality/subdomain/lookalike suffix,
   host-only contrast, root/exact/trailing slash/segment/case, transport unknown,
   expiry before/exact/after, session/unknown/noncanonical and combined mismatch+unknown.
   Fix complete expected bytes/statistics/reasons without running future model; hash
   all five before code. Clear malformed versus unsupported expectations. Done when
   source links, hand derivations and two repaired positives per negative family exist.
2. Core/admission slice: five cookielab modules, then focused tests in a separate
   slice. Definition: exact frozen reports/diagnostics, callback sentinel/cycle/alias/
   integer/depth/size bounds and no input mutation. Test domain/path independently
   using literal finite truth tables, not copies of model formulas. Unknowns survive.
3. CLI/delivery/verifier slice: tests/test_cli.py and tools/verify.py plus focused
   docs. Definition: full fixture bytes normal/-O; inert rendering, fresh-file and
   exact write/failure statuses; live pipe barrier/closed streams; stress receipts.
   Forbidden-capability checks cover imports/callers, no upstream imports or network.
   Four isolated semantic mutants: host-only omission, suffix-dot omission,
   slash-boundary omission, expiry `<` instead of `<=`; fifth unknown-to-pass mutant.
   Each must fail intended assertions with zero harness errors and exact restoration.
4. Review/portfolio closeout: ECC actual-code SELF review (not independence), SAST
   app/test/tool scoped results with narrow justified harness exceptions only;
   rerun affected checks after fixes. README setup/demo/architecture/security/limits,
   SECURITY.md/MIT license/attribution/AI disclosure; STATE/DECISIONS/LEARNING and
   concise Obsidian milestone. Hash/current receipts reconcile docs with raw results.
   Create the authorized public repository and verify hosted tests, Bandit and CodeQL.
   Preserve failures and the pre-core freeze.

All stages are sequential. Finish this current task and stop; no successor lab or
scope expansion is authorized.
