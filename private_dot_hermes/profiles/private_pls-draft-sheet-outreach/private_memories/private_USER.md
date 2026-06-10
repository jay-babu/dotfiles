User: RO OK; ask before mutations/reruns; plan-only means no changes; approve criteria+format; close loops; UI fixes require local-branch browser verify, not prod; full tests; code changes validate+commit+push unless told not; no Slack fence lang tags.
§
User prefers mise for installs and uv for Python deps/scripts when practical; global installs ok otherwise.
§
User prefers high-level architecture talk first; Kanban pipeline runs should have minimal input, with steps in workflow contracts.
§
User expects pos-db schema migrations to avoid DO blocks/conditional procedural DDL because sqlc and bob need to parse them; use plain SQL such as DROP CONSTRAINT IF EXISTS then ADD CONSTRAINT.
§
Jay Patel prefers to be @mentioned as <@U068K4E4DFC> in final review messages for tasks he initiates by messaging the agent directly; do not tag him for webhook-originated or cron-originated tasks.
§
User prefers routine chezmoi persistence: re-add appropriate target changes, commit, and push directly to the dotfiles repo without opening PRs; leave unrelated AWS_PROFILE changes unstaged unless explicitly requested.
§
Jay triages rare external/native/library crashes as no-fix when impact is very low; fix low-volume app-logic bugs, and fix external issues when impact is high.
§
Retail recs: use aggregate demo/cultural fit with POS; no individual inference.