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

Pitfall: many machines can `git push` because a credential helper is configured even when `gh` and `GITHUB_TOKEN` are absent. Conversely, `~/.config/gh/hosts.yml` may contain a usable GitHub token even when the `gh` binary is not installed and `git push` has no credentials. For API PR creation/check polling, use `git credential fill` or the gh hosts token as fallbacks, but never echo credential values. When testing push credentials, set `GIT_TERMINAL_PROMPT=0` so missing credentials fail fast instead of hanging.

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

```bash
# From likely repo parent locations
find /root/code -maxdepth 3 \( -name .git -type f -o -name .git -type d \) 2>/dev/null | head

# Inside an existing checkout/worktree
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

Branch naming conventions:
- `feat/description` — new features
- `fix/description` — bug fixes
- `refactor/description` — code restructuring
- `docs/description` — documentation
- `ci/description` — CI/CD changes

### Worktree/branch hygiene for incident or hotfix PRs

Before committing, especially in repos with multiple worktrees, submodules, or generated files, verify the branch and staged scope:

```bash
git branch --show-current
git worktree list
git status --short
git diff --cached --name-only
```

If a fix was accidentally committed on the wrong branch or alongside unrelated dirty files, do not open a PR from that branch. Create or switch to a clean branch/worktree from the intended base, cherry-pick only the intended commit or re-apply only the intended files, then verify `git diff --name-only <base>...HEAD` contains only the PR's files. This prevents unrelated generated/model/submodule changes from leaking into urgent PRs.

## 2. Making Commits

### Submodule-backed schema/API changes

When a PR changes API/model definitions stored in a git submodule, make a real branch+commit in the submodule, push it, then commit the parent repo's submodule pointer plus any parent tests/code. See `references/submodule-api-schema-prs.md` for the full workflow and pitfalls.

Use the agent's file tools (`write_file`, `patch`) to make changes, then commit:

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

Commit message format (Conventional Commits):
```
type(scope): short description

Longer explanation if needed. Wrap at 72 characters.
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`

## 3. Pushing and Creating a PR

### Push the Branch (same either way)

```bash
git push -u origin HEAD
```

### Create the PR

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
- If PR creation returns HTTP 422, check whether an open PR already exists for the same head branch (`GET /repos/{owner}/{repo}/pulls?head={owner}:{branch}&state=open`) before treating it as a hard failure.
- Avoid shell-quoting bugs for long PR bodies: write the body to a temp file and have a short Python/JSON script read it and call the REST API, rather than interpolating multiline Markdown into a shell JSON string.

## 4. Monitoring CI Status

### Check CI Status

Before polling, know what counts as actionable:
- Query both the combined commit status endpoint and the check-runs endpoint; modern GitHub Actions normally appear as check runs, while integrations may still use commit statuses.
- GitHub's combined commit status can remain `pending` even when all visible check runs are `completed / success` (for example when no legacy statuses exist or a separate expected status has not reported). Report the per-check-run results explicitly rather than treating combined-status `pending` alone as a failure.
- A failed integration/agent check can be infrastructure noise rather than a code failure. Inspect logs before changing code. Examples: Stably reporter authentication/config failures (`STABLY_API_KEY`/`STABLY_PROJECT_ID`), autoheal context fetch failures, or Pulumi preview comment failures caused by GitHub/Octokit timeouts after the preview itself completed.
- For transient infrastructure failures on a single GitHub Actions job, rerun the failed job via REST (`POST /repos/{owner}/{repo}/actions/jobs/{job_id}/rerun`) or `gh run rerun --failed` when available, then poll again instead of changing code.
- After rerunning a check, the check-runs endpoint may contain multiple runs with the same name. When deciding whether CI is green, group by check name and use the latest `started_at`/run for each name; otherwise an older failed run can mask a successful rerun.
- If a required check remains `in_progress`, continue polling when possible; if tool/time limits stop you, report the last observed state precisely instead of saying checks passed.

**With gh:**

```bash
# One-shot check
gh pr checks

# Watch until all checks finish (polls every 10s)
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
