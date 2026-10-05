# Cookie scope source comparison

## Primary sources and interpretation

- [RFC 6265](https://www.rfc-editor.org/rfc/rfc6265.html), especially 5.1.3–5.1.4,
  5.3–5.4: distinguishes storage from retrieval. Domain suffix needs a dot boundary;
  host-only scope needs equality. Path comparison has slash boundaries. Default path
  derives from the setting request, not a later sending request. Retrieval permits
  user-agent omission. Public-suffix rejection is a storage/admission concern.
- [HTTPWG 6265bis draft](https://httpwg.org/http-extensions/draft-ietf-httpbis-rfc6265bis.html),
  inspected October 5: displayed September 30, 2026 and expiration April 3, 2027.
  Work in progress, not a finalized replacement standard. SameSite involves request
  context and navigation; setting and delivery rules differ. Origin equality cannot
  substitute for site computation. Current-browser policy is not established here.
- [Python cookiejar documentation](https://docs.python.org/3/library/http.cookiejar.html):
  Netscape/RFC2965 compatibility and explicit strictness switches. The class is not
  an oracle for full browser behavior. Runtime inspected source is separately pinned;
  latest online documentation is not evidence of the installed interpreter version.

Default-path teaching belongs in the README: `/app/page` defaults to `/app`, whereas
`/app` defaults to `/`. This lab receives an already stored absolute cookie path and
never computes it from the current sending request. Raw Domain/Path attributes,
Max-Age/Expires precedence, date parsing, setting rejection and replacement are out.

Use an explicit conservative integer expiry contract: persistent cookies are expired
when `expires_at <= now`. Both inspected CPython Cookie.is_expired and aiohttp heap
expiration use equality-inclusive comparison. This is a frozen lab resolution at
whole-second precision, not a claim about all browser clocks or floating-point jars.
Session lifetime is outside the model; records assume the cookie is still retained.

## Strongest candidates inspected through connected GitHub

| Candidate | Pinned source and maintenance | Fit and decision |
|---|---|---|
| CPython http.cookiejar | [9133d5c2cb4ace240306f151b54c52a47136af81](https://github.com/python/cpython/tree/9133d5c2cb4ace240306f151b54c52a47136af81), head October 5 09:10:14Z | Inspect domain/path/secure/expiry policy, relevant tests and license. Useful reference, no dependency or borrowed implementation. Legacy defaults and real-cookie handling exceed this profile. |
| aiohttp CookieJar | [766b882820da0651c84090e366a3b024b4a263c9](https://github.com/aio-libs/aiohttp/tree/766b882820da0651c84090e366a3b024b4a263c9), head October 4 23:04:28Z | Modern storage/filter implementation, explicit host-only tracking, expiry, IP policy, secure-origin overrides, resource limits. Useful source/testing comparison; framework and real values/storage/network integrations are unnecessary. |

Actual captures: CPython Lib/http/cookiejar.py, Lib/test/test_http_cookiejar.py,
LICENSE, workflow directory and build.yml; aiohttp aiohttp/cookiejar.py,
aiohttp/_cookie_helpers.py, tests/test_cookiejar.py, pyproject.toml, LICENSE.txt,
docs/client_advanced.rst, workflow directory and ci-cd.yml. Inspected selected
callers/filtering/admission and fixed path/domain tests; not an exhaustive code audit.

CPython default DomainLiberal differs from enforcing strict host-only semantics;
return_ok_domain optionally applies DomainStrictNonDomain. Its path-return check
has the slash boundary. Runtime cookiejar is stdlib; the whole CPython source/build
tree is not a suitable package fork. PSFv2 plus historical/component notices must be
preserved if copying becomes necessary; current plan copies no upstream code.

aiohttp depends on aiohappyeyeballs, aiosignal, frozenlist, multidict, propcache,
yarl and version-conditional async-timeout/typing_extensions. pyproject declares
Apache-2.0 AND MIT, with Apache LICENSE.txt and vendored llhttp notice requirements.
The framework builds native/optional components and has pytest/freezegun tests;
not installing it removes an unnecessary supply-chain surface for this particular
profile, not proof that stdlib is universally safer. Defined CI includes pytest
jobs; CPython defines build/test jobs. No upstream CI run was checked or executed.
No Scorecard result or comprehensive advisory audit was obtained.

Bounded issue evidence: [aiohttp PR13943](https://github.com/aio-libs/aiohttp/pull/13943)
was merged October 4 and is the pinned domain-matching performance change. This
supports recent maintenance, not independent security validation. [CPython89773](https://github.com/python/cpython/issues/89773)
contains a migrated historical ordering discussion; migration fields are not current
issue status. Header ordering is outside this lab. Search also surfaced historical
invalid-cookie-attribute discussion89521; no exploit or current vulnerability claim.

Connected repository search `python cookiejar`, four results, surfaced browser-jar
and encrypted-jar projects; they did not improve metadata-only fit. They were not
deeply audited. Initial generic fetch of /search/repositories returned400 and initial
aiohttp head fetch failed transport; correct connector search and subsequent pinned
fetches succeeded. Later primary-web find request failed connection; earlier actual
RFC/draft/documentation reads remain the evidence. Searches were bounded, not exhaustive.
No upstream source was executed, installed, cloned or added to an application path.

## Profile comparison

Narrow scope: stored host-only/domain/path/secure/expiry plus supplied request host,
path, transport and clock. Four independent gates, conditional eligibility only.
Finite checks, fixed expected reports and mutation controls can demonstrate errors.

Broader SameSite: needs separately declared site-for-cookies, top-level/document
context, navigation/method/redirect assumptions, explicit cookie policy/defaults,
and a chosen version of evolving draft/browser behavior. PSL/site calculations and
browser exceptions create additional dependencies or large excluded contexts.
Recommendation: defer that profile; no same-origin-to-same-site shortcut or permissive
default. Records requesting SameSite/partitioning/browser policies are unsupported.

