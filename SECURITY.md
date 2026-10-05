# Security model

This is a learning model of supplied metadata, not a browser-cookie security product.
Protected assets are honest results, bounded admission and local output integrity.
Caller declarations are untrusted data; trusted application code fixes the schema,
profile and limitations. Caller content cannot introduce an action, executable code,
trusted identity or permissive policy.

An attacker can submit misleading/unknown metadata, malformed JSON, oversized/deep
trees, custom Python objects and output-injection text. Whole admission rejects
callbacks/subclasses/cycles before coercion; gates retain independent failures and
unknowns; output is inert/escaped and checked before delivery. Unsupported context
never grants eligibility. Privileged execution is not implemented anywhere in this lab.

Residual risks: dishonest supplied secure/time/storage context, excluded setting and
browser policy, unknown real user-agent behavior, OS resources and trusted CLI path
races. Input/output caps do not contain malicious imported code or guarantee hard
memory/time isolation. Do not import cookies, credentials, private logs or production
session data. There is no data collection, cloud API or network listener.

Raw prompts and research coordination records are excluded from the public repository.
Only synthetic fixtures and reviewed project code/documentation are published. Local
checks and GitHub scanning findings are distinct from an independent security audit.
Report a suspected code defect privately through GitHub's security advisory mechanism
when available; public issue reports should contain inert synthetic reproductions.
