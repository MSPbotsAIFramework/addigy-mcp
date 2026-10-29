# PRD-21195 · Code review

## Round 1 · 2026-10-29 · reviewed bc3e3b9 (base 018e53e)

Verdict: approved

### Findings

None. `git diff origin/main...bc3e3b9` touches only `docs/tickets/PRD-21195.md` and `docs/tickets/PRD-21195.ac.json` (2 files, 296 insertions, 0 deletions) — no source code, tests, README, or dependency files were changed, matching the design and dev legs' conclusion that `addigy-mcp` was already a complete, SOP-compliant implementation and no code change was needed.

Independently spot-checked (not re-run blind from the self-test section) against the pre-existing, unmodified implementation:

- `src/addigy_mcp/server.py:29-69` (`GatewayTokenMiddleware`): requires `X-Addigy-Api-Key` on every `/mcp` request, returns 401 with `required_headers` when missing, stores the key in a `contextvars.ContextVar` reset in a `finally` block — matches the design doc's credential-isolation claims and the SOP's per-request isolation requirement.
- 5 tools registered (`src/addigy_mcp/tools/{devices,alerts,policies,apps}.py`: `addigy_query_devices`, `addigy_get_alerts`, `addigy_query_policies`, `addigy_query_installed_apps_agent`, `addigy_query_installed_apps_mdm`), all `readOnlyHint=True` — matches README's Tool List table and the Self-test section's live `tools/list` result.
- `README.md` lines 7-71 (the `<div align="center">` opener through the `## MSPbots Connector` block, up to the next heading) is byte-identical to `~/.claude/skills/vendor-mcp-development/reference/readme-connector-section.md`, aside from one trailing blank line before the next markdown heading (immaterial whitespace, not a content difference).
- Chinese-text scan (`grep -rnP '[\x{4e00}-\x{9fff}]' --exclude-dir=.git --exclude-dir=.venv .`) confirms the only 2 hits are in the design doc itself (`docs/tickets/PRD-21195.md`: a quoted ClickUp comment and the `[需求缺失/INCOMPLETE]` SOP marker) — none in `src/`, `tests/`, or `README.md`.
- `docs/tickets/PRD-21195.ac.json` parses as valid JSON with 8 well-formed cases, matching the 8 test cases described in the main doc.

No must-fix, no suggestions. TC-ADDIGY-001 through 007 are correctly deferred to this leg's INT publish + health check per the 2026-10-29 three-stage process (they require live gateway admin/tenant API access that the dev leg does not have); TC-ADDIGY-008 is automated, passed, and reproduced live.

Status: frozen @ bc3e3b9

### Fixes

n/a — first round, no prior findings.
