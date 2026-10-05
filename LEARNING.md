# Learning notes

Host-only scope and a Domain attribute are different even when stored domain strings
look identical. `badexample.test` is not a subdomain of `example.test`. Similarly,
`/apple` does not match stored `/app`; `/app/x` does. Default path was chosen at setting
time, not from the later request being tested.

Eligibility is a conjunction of narrow checks under assumptions, not a permission or
delivery guarantee. A known mismatch can establish exclusion while another gate
remains unresolved. That distinction belongs in the full output, not just a boolean.

Python's bool is an int subclass, and arbitrary objects can execute callbacks during
equality/iteration/coercion. Native admission checks exact type identity first, counts
aliases repeatedly and rejects cycles before serialization. Output stream counts must
also be exact integers; a truthy return is not proof that bytes were delivered.

The first test harness used Windows sandbox TEMP, which denied file access. Test-owned
temporary directories moved into the workspace; no application contract was changed.
The first local source-reading search used shell-incompatible brace syntax; corrected
explicit paths. Neither failure was a cookie-model result.

Local drafting gave incorrect domain/path advice during research; it was rejected.
The implementation README local route was unavailable and one free remote attempt
returned no text. Model output was never authority or an oracle.

Optional exercise: change a fixture from domain scope to host-only and predict which
subdomain result changes; then change only the supplied clock to exact expiry time.

A capability check initially treated fixed re.compile as Python code compilation.
The corrected AST check distinguishes attribute calls from builtin compile; the
failed verifier receipt is preserved and excluded from passing claims.
