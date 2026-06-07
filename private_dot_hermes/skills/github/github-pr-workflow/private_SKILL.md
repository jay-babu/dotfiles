---
name: github-pr-workflow
description: "GitHub PR lifecycle: branch, commit, open, CI, merge."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Pull-Requests, CI/CD, Git, Automation, Merge]
    related_skills: [github-auth, github-code-review]
---

# GitHub Pull Request Workflow

Complete guide for managing the PR lifecycle. Each section shows the `gh` way first, then the `git` + `curl` fallback for machines without `gh`.

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- Inside a git repository with a GitHub remote

### Quick Auth Detection

```bash
# Determine which method to use throughout this workflow
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  # Ensure we have a token for API calls. Do not print token values.
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2- | tr -d '\n\r' | sed 's/^['\''"]//; s/['\''"]$//')
    elif [ -n "$GH_TOKEN" ]; then
      GITHUB_TOKEN="$GH_TOKEN"
    elif [ -n "$GITHUB_PAT" ]; then
      GITHUB_TOKEN="$GITHUB_PAT"
    elif git credential fill >/tmp/github-cred.$$ 2>/dev/null <<<'protocol=https
host=github.com
'; then
      GITHUB_TOKEN=$(awk -F= '$1=="password" {print $2; exit}' /tmp/github-cred.$$)
      rm -f /tmp/github-cred.$$
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi
echo "Using: $AUTH"
[ -n "$GITHUB_TOKEN" ] && echo "GitHub API credential: available" || echo "GitHub API credential: missing"
```

Pitfall: many machines can `git push` because a credential helper is configured even when `gh` and `GITHUB_TOKEN` are absent. Conversely, `~/.config/gh/hosts.yml` may contain a usable GitHub token even when the `gh` binary is not installed and `git push` has no credentials. If the user prefers mise-managed tools, `gh` may be installed under `~/.local/share/mise/installs/github-cli/<version>/.../bin/gh` but not on PATH; probe that location before falling back to raw REST. For API PR creation/check polling, use `git credential fill`, a mise-installed `gh`, or the gh hosts token as fallbacks, but never echo credential values. When testing push credentials, set `GIT_TERMINAL_PROMPT=0` so missing credentials fail fast instead of hanging; if a credential-helper command still times out or is blocked, do not retry the same command—switch to another credential source such as the gh hosts file.

### Extracting Owner/Repo from the Git Remote

Many `curl` commands need `owner/repo`. Extract it from the git remote:

```bash
# Works for both HTTPS and SSH remote URLs
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
echo "Owner: $OWNER, Repo: $REPO"
```

---

## 1. Branch Creation

Before cloning a repository or creating a new worktree, check whether the repo is already organized as a worktree collection and reuse the existing branch worktree when present. Users may expect this; cloning over/around an existing worktree wastes time and can put changes in the wrong checkout.

For Transformity repos under `/root/code`, use the canonical existing worktree manager/root and create new branch worktrees **inside that manager directory**, sibling to `main/` — do not create parallel clone families or top-level `../Repo-pd-*` directories:

- Zeus: `cd /root/code/zeus && git worktree add pd-<id>-<slug> -b fix/pd-<id>-<slug> origin/main`
- Frontend: `cd /root/code/TransformityPOSFrontend && git worktree add pd-<id>-<slug> -b fix/pd-<id>-<slug> origin/main`
- Backend: `cd /root/code/POSBackend && git worktree add pd-<id>-<slug> -b fix/pd-<id>-<slug> origin/main`

Example matching the user's convention: `cd /root/code/TransformityPOSFrontend && git worktree add backup-main` creates `/root/code/TransformityPOSFrontend/backup-main`, next to `/root/code/TransformityPOSFrontend/main`.

If multiple possible roots exist (for example `POSBackend` and `POSBackend-main`), first run `git worktree list` from the canonical repo root above and reuse that family unless the user explicitly points to another checkout.

For cleanup of accidental worktree sprawl, stale `.git/worktrees/...` pointer directories, duplicate `POSBackend-main`-style families, and dirty-worktree backup-before-delete handling, see `references/transformity-worktree-cleanup.md`.

```bash
# From likely repo parent locations
find /root/code -maxdepth 3 \( -name .git -type f -o -name .git -type d \) 2>/dev/null | head

# Inside the canonical existing checkout/worktree manager, not an arbitrary sibling
git worktree list
git branch -a | grep -i '<topic-or-pr-keyword>'
```

This part is pure `git` — identical either way:

```bash
# Make sure you're up to date
git fetch origin
git checkout main && git pull origin main

# Create and switch to a new branch
git checkout -b feat/add-user-authentication
```

Pitfall: some local worktree-manager/bare checkouts can have unusual or missing `remote.origin.fetch` refspecs, so `git fetch origin` may not update `refs/remotes/origin/main`. If a requested commit appears not to be on `origin/main` but does appear on local `main`, verify the real remote default branch with `git ls-remote origin refs/heads/main` and compare `git rev-parse main` / `git rev-parse origin/main` before choosing a base. For a simple revert PR, branch from the checkout's current `main` only after confirming it matches the remote `refs/heads/main`.

Pitfall: repository post-checkout hooks may fail during `git worktree add` after the worktree and branch were already created (for example code generation hook fails because `bun` is not installed). Do not assume the worktree add failed entirely. `cd` into the new worktree, check `git branch --show-current` and `git status --short`, then continue if the branch and files are usable; only fix the hook/tooling if it blocks the actual PR task.

Branch naming conventions:
- `feat/description` — new features
- `fix/description` — bug fixes
- `refactor/description` — code restructuring
- `docs/description` — documentation
- `ci/description` — CI/CD changes

### Worktree/branch hygiene for incident or hotfix PRs

Before committing, especially in repos with multiple worktrees, submodules, generated files, frontend build artifacts, or service workers, verify the branch and staged scope:

```bash
git branch --show-current
git worktree list
git status --short
git diff --cached --name-only
```

If running local frontend tests/builds modifies generated or dev-server artifacts (for example `public/mockServiceWorker.js` from MSW/service-worker tooling) and that file is not part of the requested change, revert it before staging. Do not let test/build side effects leak into otherwise focused feature PRs; stage explicit intended paths and re-run `git status --short`/`git diff --check` before commit.

If a fix was accidentally committed on the wrong branch or alongside unrelated dirty files, do not open a PR from that branch. Create or switch to a clean branch/worktree from the intended base, cherry-pick only the intended commit or re-apply only the intended files, then verify `git diff --name-only <base>...HEAD` contains only the PR's files. This prevents unrelated generated/model/submodule changes from leaking into urgent PRs.

When a PR introduces a new config-driven pattern, migrate the existing/default case into that same pattern instead of leaving the old value hardcoded with a separate “additional” escape hatch. Reviewers should see one source of truth for current and future cases; if avoiding a diff is important, make the config contain the current value and verify preview shows no behavioral change.

## 2. Making Commits

### Submodule-backed schema/API changes

When a PR changes API/model definitions stored in a git submodule, make a real branch+commit in the submodule, push it, then commit the parent repo's submodule pointer plus any parent tests/code. See `references/submodule-api-schema-prs.md` for the full workflow and pitfalls.

For Zeus `libs/model/pos-db` database migration work, the PR usually belongs directly in the `Transformity/pos-db` submodule repo rather than the parent Zeus repo. See `references/pos-db-migration-prs.md` for Atlas/Squawk/concurrent-index/FK-validation workflow details and CI pitfalls.

When adding or maintaining cross-repo CI that runs Zeus tests from a `pos-db` PR, see `references/pos-db-zeus-ci.md` for the proven checkout/overlay pattern, generation command, test scoping, and CI-failure interpretation pitfalls.

For Transformity POSBackend PRs, see `references/posbackend-pr-workflow.md` for fresh-clone/submodule setup, Gradle verification commands, Testcontainers Docker-subnet cleanup, REST PR creation when `gh` is absent, and POSBackend-specific CI interpretation notes.

For Transformity POS frontend PRs, see `references/transformity-frontend-pr-workflow.md` for canonical worktree placement, Node 22/mise validation, frontend artifact hygiene, focused table sort-column-id fixes, and the workflow for superseding backend workaround PRs with frontend fixes. For npm-to-Bun/Vite migration follow-ups, see `references/transformity-frontend-bun-vite-finalization.md` for `bunx --bun vite` script alignment, Amplify cache guardrails, Playwright/Stably `npx` exceptions, and validation/CI interpretation notes.

For cross-repo API/client fixes where a frontend parameter depends on backend endpoint support or generated client types, see `references/cross-repo-api-client-prs.md`. Verify both the frontend generated type and the backend endpoint before relying on a minimal UI diff; a temporary `@ts-expect-error` should be treated as a bridge until the backend/API model/client regeneration supports the parameter, not as proof the API already accepts it. When a page has a CSV/export action, compare the page data query params against the export query params and backend export endpoint for filter parity: selected entities/stores, sales channels, vendors, vendor selection mode, tags, departments, and search terms should usually match; pagination and sort are not filters and may intentionally be omitted from full-export requests. Also trace downstream export-only data paths (for example historical/monthly columns or secondary repository calls) so selected filters apply consistently beyond the main/current-period totals query.

For Zeus/Kurama PRs that touch HTMX templates, web assets, or model SQL, see `references/zeus-kurama-generated-prs.md` for required `go generate` commands, targeted validation, generated-file staging expectations, and how to report broad Atlas/Testcontainers integration failures.

For upstream third-party JavaScript GitHub Action PRs, see `references/upstream-js-action-prs.md` for fork setup, committed `dist/` output, mise/Corepack/Yarn validation, Husky commit pitfalls, and fork-PR CI `action_required` interpretation.

Use the agent's file tools (`write_file`, `patch`) to make changes, then commit. If the repository uses Husky/lint-staged and the user's Node toolchain is managed by mise, run the commit itself through mise so hooks use the intended `node`/`npx` binaries:

```bash
mise exec node@22 -- git commit -m "fix: handle rejected customer update mutations"
```

Then commit normally when no toolchain wrapper is needed:

```bash
# Stage specific files
git add src/auth.py src/models/user.py tests/test_auth.py

# Commit with a conventional commit message
git commit -m "feat: add JWT-based user authentication

- Add login/register endpoints
- Add User model with password hashing
- Add auth middleware for protected routes
- Add unit tests for auth flow"
```

Pitfall: a plain `git commit` can fail inside Husky hooks with errors like `/usr/local/bin/npx: ... /tmp/node-v22.../bin/npx: not found` even after tests passed under `mise exec node@22 -- npm ...`. Retry the commit through the same mise Node version before changing code or bypassing hooks.

Pitfall: isolated git worktrees may contain `.husky/pre-commit` but be missing `.husky/_/husky.sh`, causing `git commit` to fail before running the real hook. Do not treat this as a code/test failure. Run the hook payload explicitly through the repo's toolchain (for example `mise exec node@22 -- npx lint-staged`), confirm it passes and restages any formatting changes, then commit with `HUSKY=0 git commit --no-verify ...` and mention the hook-bootstrap issue if relevant.

Commit message format (Conventional Commits):
```
type(scope): short description

Longer explanation if needed. Wrap at 72 characters.
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`

## 3. Pushing and Creating a PR

### Push the Branch (same either way)

For this user, code changes are not complete when they are only committed locally. After making code changes, run local validation, commit, and push the branch unless the user explicitly says not to push. Do not stop at “left as local uncommitted changes” or “committed locally” for normal code-fix work; if pushing is blocked, report the blocker and the exact local commit SHA.

```bash
git push -u origin HEAD
```

If a normal push or force-push hangs/timeouts but gh auth is configured, retry once with terminal prompts disabled and the gh credential helper explicitly wired. For force-pushes after an amend, capture the old remote SHA first and use an explicit lease:

```bash
BRANCH=$(git branch --show-current)
OLD_REMOTE_SHA=$(git ls-remote origin "refs/heads/$BRANCH" | awk '{print $1}')
GIT_TERMINAL_PROMPT=0 git \
  -c credential.helper='!gh auth git-credential' \
  push origin "HEAD:refs/heads/$BRANCH" \
  --force-with-lease="refs/heads/$BRANCH:$OLD_REMOTE_SHA"
```

When `gh` is mise-installed but not on PATH, replace `gh` in the helper with the absolute mise binary path.

If the wrapper blocks that push with a hard “do not retry this command” timeout, switch strategies rather than retrying the same git push. If the desired tree already exists locally but local HEAD was amended/diverged from the remote branch, create a normal descendant commit from the current remote branch and push that commit (no force required):

```bash
BRANCH=$(git branch --show-current)
REMOTE_REF="refs/remotes/origin/$BRANCH"
NEW_SHA=$(git commit-tree HEAD^{tree} -p "$REMOTE_REF" -m "Format/fix follow-up")
git push origin "$NEW_SHA:refs/heads/$BRANCH"
```

This is useful for formatting-only follow-ups after a blocked force-push: it preserves the remote PR history, avoids retrying a blocked force-push, and updates the branch with a normal fast-forward commit. Verify `git rev-parse HEAD` versus `git rev-parse $REMOTE_REF` afterward because local HEAD may still point at the amended commit rather than the pushed `commit-tree` commit.

For more complex or file-specific changes, use the GitHub REST Git API as a safe fallback: read the branch ref, create blob(s) for changed file contents, create a tree with `base_tree` from the branch head, create a commit with the branch head as parent, then PATCH `git/refs/heads/<branch>` to the new commit SHA. This avoids shell/credential-helper push hangs; print only old/new SHAs and the PR URL, never token or credential-helper output.

### Create the PR

For cross-repo changes, keep branch names aligned where practical (for example the same `fix/<topic>` in each repo), create one PR per repository, and report them back as a compact list grouped by repo. Before the final user note, run `git status --short` in each changed worktree and include honest validation notes: codegen/formatting that passed, tests that failed or were blocked, and the known cause when available. Do not imply the batch is fully green if any repo's local tests failed or were environment-blocked.

When polling or editing multiple PRs across different repositories, scope every `gh` command to the correct repo/worktree. Do not run `gh pr checks <number>` for a frontend PR while the shell cwd is in a backend repo; PR numbers are repo-local and GitHub will report misleading “could not resolve PullRequest” errors. Prefer explicit subshells such as `(cd /path/to/frontend && gh pr checks 2712 ...)` and `(cd /path/to/backend && gh pr checks 1802 ...)` inside combined pollers.

Verification wording must distinguish test/build/CI evidence from manual product verification. Do not say or imply “browser tested”, “UI verified”, “done”, or “end-to-end verified” unless you actually exercised the authenticated user flow in a browser (or an equivalent E2E test) and saw the expected behavior. If the original user request explicitly asked to debug/test “using the UI,” make a real post-fix browser attempt before the final PR report; if auth/entity access blocks the target screen, report it prominently as “not manually UI-verified due <specific blocker>,” not as a completed UI test. If you could only start the app and reach a login screen, report that precisely as “app loaded to login; authenticated flow not manually verified here.”

For frontend UI PRs, especially when adding navigation, buttons, tabs, or links to an existing page, include an explicit visual placement check before reporting done or pushing for review. Inspect the actual page/component in a browser when authenticated access is available; if auth blocks the full app, build a temporary local probe/story-style harness using the real component/layout and remove it before committing. Verify the element is in the intended UI region (for example existing tab/sidebar group rather than page content) and that the final report states exactly what was visually checked and any limits.

**With gh:**

```bash
gh pr create \
  --title "feat: add JWT-based user authentication" \
  --body "## Summary
- Adds login and register API endpoints
- JWT token generation and validation

## Test Plan
- [ ] Unit tests pass

Closes #42"
```

Options: `--draft`, `--reviewer user1,user2`, `--label "enhancement"`, `--base develop`

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{
    \"title\": \"feat: add JWT-based user authentication\",
    \"body\": \"## Summary\nAdds login and register API endpoints.\n\nCloses #42\",
    \"head\": \"$BRANCH\",
    \"base\": \"main\"
  }"
```

The response JSON includes the PR `number` — save it for later commands.

To create as a draft, add `"draft": true` to the JSON body.

Pitfalls:
- If `gh` is not installed after you have already pushed the branch, do not stop. Use the REST `POST /repos/{owner}/{repo}/pulls` fallback with a token from `git credential fill` or another configured source, and print only PR number/URL/SHA.
- If `gh pr create` says you must first push the current branch even after `git push -u origin HEAD` succeeded, verify the remote ref with `git ls-remote --heads origin "$BRANCH"` and retry with explicit `--head "$BRANCH" --base main`; do not repush or recreate the worktree just to satisfy gh's local upstream detection.
- If PR creation returns HTTP 422, check whether an open PR already exists for the same head branch (`GET /repos/{owner}/{repo}/pulls?head={owner}:{branch}&state=open`) before treating it as a hard failure.
- If an existing PR was closed and `gh pr reopen`/GraphQL cannot reopen it, do not keep trying to mutate stale PR state. Create a replacement PR from the corrected head branch, update/comment the closed PR as superseded, and report both links plus the reason. Verify the new PR's `head.sha` matches the branch ref because closed PRs can appear stuck on an old head even after the branch moves.
- Avoid shell-quoting bugs for long PR bodies: write the body to a temp file and have a short Python/JSON script read it and call the REST API, rather than interpolating multiline Markdown into a shell JSON string.
- If the terminal wrapper blocks or times out while running a long inline/temp-file Python PR creation script, clean up the temp file and retry the minimal REST call with `execute_code`. Keep the same secret-handling rules: read `git credential fill` internally, print only PR number/URL/SHA, and never echo tokens or raw credential-helper output.

## 4. Monitoring CI Status

### Addressing PR review comments and conversation threads

When the user asks to “review/address/resolve comments,” treat GitHub review conversations as part of the work, not just code suggestions:

1. Fetch review comments and conversation threads before editing, and identify which comments require code changes versus explanation/no-op.
2. If a reviewer/user objects to the shape of the implementation, reassess the design before defending or minimally patching it. Prefer simpler explicit call sites over clever reuse that changes edge-case semantics, relies on zero-value branches, or needs carve-outs to preserve behavior. A review comment like “we are taking advantage of an edge case” is usually a design correction, not just a request for an explanatory reply.
3. When review feedback asks for an existing pattern or “minimal diff,” remove agent-added scaffolding that was only introduced for testability or abstraction unless it is explicitly needed. For example, in frontend table-sort fixes, prefer adding the required TanStack column `id` inline on the existing accessor over extracting the whole column list into a helper and adding a broad test just to observe the column config. Verify the final PR file list/diff shows the minimal intended change before pushing.
4. After committing and pushing fixes, resolve the specific review threads you addressed. Use the thread IDs from the PR review-thread API/GraphQL rather than assuming a comment is resolved because a commit exists.
4. Verify the result by querying unresolved review threads again and report the count (for example “GitHub reports 0 unresolved threads”).
5. Keep the final note compact: PR URL, commits pushed, comments resolved, local validation, and any still-running or unrelated CI blockers. Do not present unrelated CI failures as caused by the review-comment fix when the diff/test evidence shows otherwise.

### Check CI Status

Before polling, know what counts as actionable:
- Query both the combined commit status endpoint and the check-runs endpoint; modern GitHub Actions normally appear as check runs, while integrations may still use commit statuses.
- GitHub's combined commit status can remain `pending` even when all visible check runs are `completed / success` (for example when no legacy statuses exist or a separate expected status has not reported). Report the per-check-run results explicitly rather than treating combined-status `pending` alone as a failure.
- A failed integration/agent check can be infrastructure noise rather than a code failure. Inspect logs before changing code. Examples: Stably reporter authentication/config failures (`STABLY_API_KEY`/`STABLY_PROJECT_ID`), autoheal context fetch failures, or Pulumi preview comment failures caused by GitHub/Octokit timeouts after the preview itself completed. If a PR's product/local checks are green but `stably-test-pr / stably-test` fails before product assertions with `[StablyAI reporter] Could not authenticate with the server...` and `fix-tests` fails to fetch autoheal context, treat it as a Stably/GitHub credential/project-config blocker rather than a product-fix failure; document the PR URL, green local/GitHub evidence, exact Stably auth signature, and next action for a Stably/GitHub admin to verify/rotate `STABLY_API_KEY` and confirm/update `STABLY_PROJECT_ID`. See `webhook-subscriptions/references/stably-pr2659-auth-blocker.md` for a concrete TransformityPOSFrontend example.
- In Zeus monorepo PRs, path/change detection can still fan out many service coverage checks. If an unrelated service coverage check fails on an unchanged service (for example `hades-price / coverage` failing because existing coverage is below threshold), inspect the log to confirm the failure signature and report it as unrelated instead of raising coverage or editing that service. Include changed-file scope and local targeted test evidence in the final PR note.
- For Zeus/Kurama incident PRs, a `kurama / coverage` failure after CI code generation can be a mainline/generated-code blocker rather than a product-fix failure, especially when unchanged packages fail to compile with generated model parameter type mismatches (for example passing `pgtype.Int8` where generated params now expect `int64`). Verify the PR diff is scoped to the intended files, cite the failing unchanged packages/signature, and report it as an unrelated CI blocker instead of broadening the incident PR.
- For `pull_request` GitHub Actions jobs, remember CI may build the synthetic merge ref (`refs/pull/<PR>/merge`), not just the branch head. If local branch tests pass but CI compile errors show old/generated types or code that does not match `HEAD`, fetch and inspect the merge ref before changing code or repeatedly rerunning jobs: `git fetch origin pull/<PR>/merge:refs/tmp/pr<PR>merge --force`, then `git show refs/tmp/pr<PR>merge:<path>`. Compare it with the branch head and the generated files the workflow uses. If the merge ref is stale or differs because of base-branch/generated-code interaction, report that precisely and refresh/rebase/regenerate against the actual merge base rather than treating a rerun alone as verification.
- For Stably PR failures, the primary `stably-test` log may hide the actual failing Playwright assertion and only show a Stably results URL plus `exit 1`. If the workflow has a follow-up `fix-tests` / `stably fix` job, inspect that job's logs too; its autoheal report often contains the actionable cause (for example backend/infrastructure replay failures) and whether code changes were intentionally not made. Treat `fix-tests` success as "autoheal completed," not proof that the original Stably failure is fixed: the report may still say `0 of N issues fully verified`, identify failures that also occur on `main`, or mention unverified/internal candidate edits. In that case, verify the PR diff scope against the failed E2E files before changing product code, and report the Stably failure as unrelated/flaky/infrastructure when there is no overlap with the PR change and local/product checks are green.
- For transient infrastructure failures on a single GitHub Actions job, inspect failed logs first, then rerun the failed job via REST (`POST /repos/{owner}/{repo}/actions/jobs/{job_id}/rerun`) or `gh run rerun --failed` when available, and poll again instead of changing code. Example: Maestro iOS smoke failures like `iOS driver not ready in time` / `LocalXCTestInstaller$IOSDriverTimeoutException` before app assertions are usually simulator/XCTest driver startup infra, not product code. Rerun the failed workflow/job unless the logs show an app assertion failure.
- After rerunning a check, the check-runs endpoint may contain multiple runs with the same name. When deciding whether CI is green, group by check name and use the latest `started_at`/run for each name; otherwise an older failed run can mask a successful rerun.
- A PR can report `mergeable_state`/state such as `blocked` even when every latest check-run is successful; this usually reflects branch protection, missing review, required conversation resolution, or merge queue policy rather than a CI failure. Report it separately as “checks green, PR blocked for merge/review policy” and do not keep rerunning checks or changing code solely because the PR state says `blocked`.
- A fork PR in a third-party repository can have no visible check-runs, combined status `pending`, and an Actions run conclusion of `action_required` until maintainers approve running workflows. Query `/actions/runs?head_sha=<sha>` when check-runs are empty; report maintainer approval required instead of treating it as a failing code check.
- A PR can report `mergeable_state: dirty` after visible checks pass because the base branch already merged overlapping work. Fetch the PR's actual `base.sha`/`base.ref` from the GitHub API, then fetch/rebase against `FETCH_HEAD` or the exact base SHA rather than trusting a stale or broken local `origin/main` ref. If the conflict shows the functional change is already present on the base branch, close/comment the PR as a duplicate/no-op instead of resolving conflicts just to recreate the same change.
- For Go repositories using `golangci/golangci-lint-action@v8` with `version: v2.1`, a fast-failing lint job may be a config/toolchain problem rather than code lint. v2 needs `version: "2"` in `.golangci.yml` plus the v2 output/exclusion schema (for example `output.formats.text.path: stdout`, `linters.exclusions.rules`, `linters.exclusions.paths`). Verify locally with `go run github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.1.6 config verify`. If the action uses `go-version: stable` and analyzer errors appear from a newer Go version than the module expects, pin `actions/setup-go` to the module's Go version before changing production code.
- For GitHub Actions deployments that are path-filtered and expensive (for example Pulumi `up` only when `iac/**` changes), do not rely only on `on.push.paths` if a failed/cancelled deployment must be retried by later app-only pushes. That pattern is edge-triggered and loses “undeployed infra debt.” Prefer running a cheap detection job on every main push (and optionally schedule/workflow_dispatch), compare `HEAD` to the latest successful workflow-run SHA for infra-relevant paths via `gh api .../actions/workflows/<file>/runs?branch=main&status=success&per_page=1`, and gate the expensive deploy job on whether infra changed since that SHA. Set deploy `concurrency.cancel-in-progress: false` so app-only pushes do not cancel the sticky retry. This workflow-level approach is simple and safe; for per-environment precision, store a deployed content hash per stack/environment (Pulumi stack tags, SSM, or S3) and compare against that instead.
- If required check remains `in_progress`, continue polling when possible; if tool/time limits stop you, report the last observed state precisely instead of saying checks passed. Long-running build checks can remain pending after quick checks like `spotless`, `preview`, and `submit-gradle` pass; do not add a final incident/PR-success note until the required build check has actually completed successfully. Job logs for in-progress runs may 302 and then return storage-provider 404/`blob does not exist`; treat that as “logs not yet available” and poll check status again rather than diagnosing from an empty log.
- If a Go GitHub Actions step like `Setup Go and cache` takes minutes, inspect the cache logs before blaming Go setup. Large `actions/cache` restores can download quickly but spend minutes extracting 1–2GB archives, especially on hosted ARM runners. Watch for service-specific jobs restoring another service's build cache via a broad restore key, commit-SHA cache keys that churn every push, and post-job cache saves adding hidden time. See `references/github-actions-go-cache-performance.md` for diagnosis and optimization patterns.
- If a `go test ./...` GitHub Actions step appears to show very fast `ok <pkg> 0.0xxs` lines but the step wall time is much longer, explain that Go's package elapsed number is test-binary runtime only; it excludes compile/link/package-loading time and output is buffered until each package completes. Pull the job log via `gh api repos/<owner>/<repo>/actions/jobs/<job_id>/logs`, compare the timestamp at `Run go test ...` with the first package result, list slow package result lines, and inspect cache hit/miss lines. A cold Go build/module cache miss can create many minutes of silence before the first `ok`, while integration packages may then report 40–90s package elapsed times. For visibility, suggest `go test -v` or `gotestsum --format pkgname`; for speed, focus on stable Go cache restore keys and avoiding commit-SHA-only/churning caches.
For GitHub Actions deployments that use protected environments and `concurrency.cancel-in-progress: false`, do not assume new commits will cancel old approval prompts.
- For autonomous incident PRs where the incident workflow requires a final PagerDuty/Slack note after CI, and a single required check is still pending near the tool time limit, start a guarded background follow-up poller rather than posting a premature final note. The poller should re-fetch PR checks and incident notes before posting; post the final note only when latest required checks pass, or a concise CI-blocker note if checks fail/time out. Print only PR/check metadata and never tokens or raw credential-helper output.

**With gh:**

```bash
# One-shot check
gh pr checks

# Compact machine-readable failures/pending checks. `gh pr checks --json` does not
# expose a `conclusion` field; use `state`/`bucket`, or use
# `gh pr view --json statusCheckRollup` when you need conclusions.
gh pr checks <PR> --json name,state,bucket,description,link \
  --jq '.[] | select(.bucket != "pass" and .bucket != "skipping") | [.name, .state, .bucket, (.description // ""), .link] | @tsv'

# Watch until all checks finish (polls every 10s). In large monorepos this can
# produce huge repeated output; prefer the compact JSON form above for agent logs.
gh pr checks --watch
```

**With git + curl:**

```bash
# Get the latest commit SHA on the current branch
SHA=$(git rev-parse HEAD)

# Query the combined status
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Overall: {data['state']}\")
for s in data.get('statuses', []):
    print(f\"  {s['context']}: {s['state']} - {s.get('description', '')}\")"

# Also check GitHub Actions check runs (separate endpoint)
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/check-runs \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for cr in data.get('check_runs', []):
    print(f\"  {cr['name']}: {cr['status']} / {cr['conclusion'] or 'pending'}\")"
```

With `gh api`, keep query parameters in the URL or pass `-X GET`; adding `-f per_page=100` without `-X GET` can make `gh` send a POST and return a misleading `HTTP 404` for endpoints such as commit check-runs:

```bash
gh api -X GET "repos/$OWNER/$REPO/commits/$SHA/check-runs?per_page=100" \
  -H "Accept: application/vnd.github+json"
```

### Poll Until Complete (git + curl)

```bash
# Simple polling loop — check every 30 seconds, up to 10 minutes
SHA=$(git rev-parse HEAD)
for i in $(seq 1 20); do
  STATUS=$(curl -s \
    -H "Authorization: token $GITHUB_TOKEN" \
    https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['state'])")
  echo "Check $i: $STATUS"
  if [ "$STATUS" = "success" ] || [ "$STATUS" = "failure" ] || [ "$STATUS" = "error" ]; then
    break
  fi
  sleep 30
done
```

## 5. Auto-Fixing CI Failures

When CI fails, diagnose and fix. This loop works with either auth method.

### Step 1: Get Failure Details

**With gh:**

```bash
# List recent workflow runs on this branch
gh run list --branch $(git branch --show-current) --limit 5

# View failed logs
gh run view <RUN_ID> --log-failed
```

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

# List workflow runs on this branch
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?branch=$BRANCH&per_page=5" \
  | python3 -c "
import sys, json
runs = json.load(sys.stdin)['workflow_runs']
for r in runs:
    print(f\"Run {r['id']}: {r['name']} - {r['conclusion'] or r['status']}\")"

# Get failed job logs (download as zip, extract, read)
RUN_ID=<run_id>
curl -s -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
  -o /tmp/ci-logs.zip
cd /tmp && unzip -o ci-logs.zip -d ci-logs && cat ci-logs/*.txt

# Alternative: a single job log endpoint returns a 302 to a short-lived signed URL.
# If following the redirect with Authorization returns a storage-provider 401,
# fetch the Location URL again without the GitHub Authorization header.
# In Python/urllib, the default opener follows the 302 and may preserve the
# GitHub Authorization header to Azure/S3, causing `InvalidAuthenticationInfo`.
# Use a no-redirect opener to capture Location, then issue a second unauthenticated request.
JOB_ID=<job_id>
curl -sD /tmp/job-log.headers \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/$OWNER/$REPO/actions/jobs/$JOB_ID/logs \
  -o /tmp/job-log.body
LOG_URL=$(awk 'BEGIN{IGNORECASE=1} /^location:/ {sub(/\r$/, "", $2); print $2}' /tmp/job-log.headers)
[ -n "$LOG_URL" ] && curl -sL "$LOG_URL" -o /tmp/job-$JOB_ID.log
```

Pitfall: if `gh` is not installed but `~/.config/gh/hosts.yml` exists, the `oauth_token` in that file can be used for REST calls. Print only that a credential key exists; never print the token or raw hosts file.

### Step 2: Fix and Push

After identifying the issue, use file tools (`patch`, `write_file`) to fix it:

```bash
git add <fixed_files>
git commit -m "fix: resolve CI failure in <check_name>"
git push
```

### Step 3: Verify

Re-check CI status using the commands from Section 4 above.

### Auto-Fix Loop Pattern

When asked to auto-fix CI, follow this loop:

1. Check CI status → identify failures
2. Read failure logs → understand the error
3. Use `read_file` + `patch`/`write_file` → fix the code
4. `git add . && git commit -m "fix: ..." && git push`
5. Wait for CI → re-check status
6. Repeat if still failing (up to 3 attempts, then ask the user)

### Sticky deploy workflows after path-filtered failures

When fixing GitHub Actions deployment workflows that currently rely on `on.push.paths` to avoid expensive deploys, check for the "failed infra deploy is never retried by later app-only commits" failure mode. First identify the exact workflow class that owns the failing IaC; do not apply the fix to a global/bootstrap deploy workflow if the user is asking about service IaC deploys. For Zeus service deploys, the expected target is the reusable service workflows (`service-ecs.yml`, `service-lambda-container.yml`, `service-pulumi.yml`) plus their `deploy-<service>.yml` callers.

A robust pattern is:

1. Remove the workflow-level `paths:` filter from the caller workflow so a cheap gate runs on every relevant branch push.
2. Add or extend an early `pending`/`changes` job that finds the latest successful run of the same caller deploy workflow on the target branch using the Actions REST API (`/repos/{owner}/{repo}/actions/workflows/<workflow-file>/runs?branch=main&status=success&per_page=1`). Use the current REST API version header (at time of writing, `X-GitHub-Api-Version: 2026-03-10`) rather than stale example values.
3. Scope `actions: read` to the cheap pending/changes job where possible, and use resilient API calls (`curl --fail-with-body --silent --show-error --retry 3 --retry-delay 2 --retry-all-errors`). In reusable workflows, remember the caller job must also grant `actions: read` as the permissions upper bound. If API lookup, JSON parse, or fetching the last successful SHA fails, fail open to `deploy_required=true` / sticky infra changed.
4. Compare that successful run's `head_sha` to `GITHUB_SHA` for only the infra-relevant paths. Prefer logging changed paths with `git log --name-only --format='' "$LAST_SUCCESS_SHA..$GITHUB_SHA" -- path1 path2 ... | sed '/^$/d' | sort -u` so CI output explains why the sticky deploy is required; `git diff --quiet` is acceptable for simpler cases.
5. For service workflows, keep app detection scoped to the current push but make infra detection sticky since latest successful deploy. Gate the expensive deploy with "sticky infra changed OR app changed and build/test succeeded" rather than forcing app builds/tests on every push.
6. Set deploy concurrency `cancel-in-progress: false`; otherwise an app-only push can cancel the in-flight infra retry that is meant to clear the pending state. The cheap pending/changes job may use `cancel-in-progress: true`.

When discussing design tradeoffs with the user, prefer exact applied-state watermarks over persistent booleans or GitHub cache. GitHub cache is not durable deployment correctness state: it can expire, be evicted, and restore-key matching can create surprising results. A repo/environment variable such as `needs_pulumi_gamma=true` is better than cache but still mutable, race-prone, requires write credentials, and does not encode which IaC version is pending. For Pulumi-backed services, store a per-service/per-environment deployed IaC content hash (for example Pulumi stack tag `deployed_iac_hash`, optionally with `deployed_iac_git_sha`) and compare it to a deterministic desired hash from tracked IaC files. Update the tag only after `pulumi up` succeeds; if it fails or is cancelled, the old hash remains and later app-only pushes keep retrying. GitHub Actions latest-success history is a fallback when target-side state is unavailable or when a single successful workflow run reconciles all environments.

Avoid adding scheduled retries unless explicitly requested. For this user's Zeus service deployment workflows, the expected fix is push-triggered stickiness in `service-ecs.yml`, `service-lambda-container.yml`, `service-pulumi.yml`, and the `deploy-<service>.yml` callers: the next normal push should re-evaluate the service/environment watermark and keep Pulumi required until a successful `pulumi up` advances the deployed hash.

Use `curl` + `python3` inside Actions instead of assuming `gh` is available on runners, unless the repo already standardizes on `gh`. For reusable service deploy workflows, also look for duplicated per-environment deploy jobs and collapse them into a matrix job when the bodies are identical; keep environment-specific side effects guarded at the step level. For full details and a known-good outline, see `references/sticky-deploy-workflows.md`. Validation: run `go run github.com/rhysd/actionlint/cmd/actionlint@latest <workflow.yml>` and `git diff --check`; if adding embedded shell/Python snippets in YAML, also extract/run `bash -n` on the generated shell scripts.

## PR branch transport fallback

If local `git push` / `git fetch` / `git reset` repeatedly times out or is blocked during PR branch repair, do not keep retrying the identical git command. When `gh api` auth works and the intended diff is small, use the GitHub Git Data API fallback in `references/git-data-api-branch-update-fallback.md` to create blobs/tree/commit and patch the PR branch ref, then verify `headRefOid` and checks.

## 6. Merging

**With gh:**

```bash
# Squash merge + delete branch (cleanest for feature branches)
gh pr merge --squash --delete-branch

# Enable auto-merge (merges when all checks pass)
gh pr merge --auto --squash --delete-branch
```

**With git + curl:**

```bash
PR_NUMBER=<number>

# Merge the PR via API (squash)
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/merge \
  -d "{
    \"merge_method\": \"squash\",
    \"commit_title\": \"feat: add user authentication (#$PR_NUMBER)\"
  }"

# Delete the remote branch after merge
BRANCH=$(git branch --show-current)
git push origin --delete $BRANCH

# Switch back to main locally
git checkout main && git pull origin main
git branch -d $BRANCH
```

Merge methods: `"merge"` (merge commit), `"squash"`, `"rebase"`

### Enable Auto-Merge (curl)

```bash
# Auto-merge requires the repo to have it enabled in settings.
# This uses the GraphQL API since REST doesn't support auto-merge.
PR_NODE_ID=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['node_id'])")

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/graphql \
  -d "{\"query\": \"mutation { enablePullRequestAutoMerge(input: {pullRequestId: \\\"$PR_NODE_ID\\\", mergeMethod: SQUASH}) { clientMutationId } }\"}"
```

## 7. Complete Workflow Example

```bash
# 1. Start from clean main
git checkout main && git pull origin main

# 2. Branch
git checkout -b fix/login-redirect-bug

# 3. (Agent makes code changes with file tools)

# 4. Commit
git add src/auth/login.py tests/test_login.py
git commit -m "fix: correct redirect URL after login

Preserves the ?next= parameter instead of always redirecting to /dashboard."

# 5. Push
git push -u origin HEAD

# 6. Create PR (picks gh or curl based on what's available)
# ... (see Section 3)

# 7. Monitor CI (see Section 4)

# 8. Merge when green (see Section 6)
```

## Useful PR Commands Reference

| Action | gh | git + curl |
|--------|-----|-----------|
| List my PRs | `gh pr list --author @me` | `curl -s -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/$OWNER/$REPO/pulls?state=open"` |
| View PR diff | `gh pr diff` | `git diff main...HEAD` (local) or `curl -H "Accept: application/vnd.github.diff" ...` |
| Add comment | `gh pr comment N --body "..."` | `curl -X POST .../issues/N/comments -d '{"body":"..."}'` |
| Request review | `gh pr edit N --add-reviewer user` | `curl -X POST .../pulls/N/requested_reviewers -d '{"reviewers":["user"]}'` |
| Close PR | `gh pr close N` | `curl -X PATCH .../pulls/N -d '{"state":"closed"}'` |
| Check out someone's PR | `gh pr checkout N` | `git fetch origin pull/N/head:pr-N && git checkout pr-N` |
