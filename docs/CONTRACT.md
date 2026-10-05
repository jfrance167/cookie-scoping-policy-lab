# Frozen contract v1

PLAN.md is the approved detailed schema/limits/threat model. Freeze supplement:
report keys in order: version, profile, results, statistics, assumptions.
Result keys: id, cookie, request, gates, unsupported_contexts, profile_status,
scope_decision. Gates ordered domain/path/transport/expiry; each has state, reason.
Reasons are DOMAIN_MATCH/DOMAIN_MISMATCH/DOMAIN_CONTEXT; PATH_MATCH/PATH_MISMATCH/
PATH_CONTEXT; TRANSPORT_MATCH/TRANSPORT_MISMATCH/TRANSPORT_CONTEXT;
EXPIRY_LIVE/EXPIRY_EXPIRED/EXPIRY_CONTEXT. Only gate state UNKNOWN adds its reason
to unsupported_contexts, in gate order, followed by supplied feature identifiers
as FEATURE:<identifier>, preserving supplied order. Noncanonical strings become
gate UNKNOWN; no raw normalization or source-setting behavior.

Statistics contains every combination of SUPPORTED/UNSUPPORTED (outer order) and
ELIGIBLE_UNDER_ASSUMPTIONS/NOT_ELIGIBLE/UNRESOLVED (inner order), including zeros,
keys '<profile_status>:<scope_decision>'.
Assumptions are the four exact strings in fixtures/expected.json. Reporting input
copies does not assert it is real metadata. JSON: ensure_ascii, indent2, LF suffix.
Markdown: heading '# Offline stored-cookie scope', subtitle in expected.md,
each result heading uses decimal entities for ID, field/value table with every
value (including structured JSON) decimal-entity escaped; assumptions escaped.
Render caps final bytes524288. All non-format encoders are private; public evaluate
admits untrusted metadata, public render re-evaluates admitted metadata.

Diagnostics fixed: INPUT_LIMIT, INVALID_JSON, JSON_DEPTH, DUPLICATE_KEY,
INTEGER_TOKEN_BOUND, NONINTEGER_JSON, TREE_TYPE, NODE_LIMIT, TREE_DEPTH,
TREE_CYCLE, CONTAINER_LIMIT, TEXT_TYPE_OR_LIMIT, TEXT_CONTROL, INVALID_UNICODE,
SCHEMA, VERSION, CASE_COUNT, ID_FORMAT, DUPLICATE_CASE_ID, NULL_TEXT_TYPE,
BOOL_TYPE, LIFETIME, TIME, EXPIRY_SHAPE, FEATURE_LIST, FEATURE_FORMAT,
FEATURE_DUPLICATE, OUTPUT_LIMIT, REPORT_FORMAT, INVALID_INPUT_PATH,
INVALID_OUTPUT_PATH, OUTPUT_EQUALS_INPUT, IO_ERROR, ARGUMENT_ERROR,
STDOUT_WRITE_AND_SILENCE_FAILED, OUTPUT_WRITE_AND_CLEANUP_FAILED.
CLI diagnostics are 'cookielab: <code>\n', fixed ASCII binary LF.
Argument errors are exit1, help successful exit0; unsupported rows exit2.

Forty expected rows are assigned by hand in the retained one-shot freeze script;
it is NOT a second semantic evaluator. It composes literal row/gate expectations,
does not inspect app code and predates the core. Fixtures/expected.json and.md are
immutable release oracles. tools/freeze_oracles.py is evidence-only, not automatically
run by verification. Sources: RFC6265 sections5.1.3/5.1.4/5.3/5.4 plus RESEARCH.md.
Expiry equality-inclusive is this explicit integer lab contract, confirmed against
pinned CPython/aiohttp source. Narrow scope has no cookie-delivery/auth verdict.
