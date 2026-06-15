# Team Rules — Lyfter Badge App

## Git Flow

We use a simplified Git Flow. The `main` branch is always production-ready. All work happens on feature branches and merges through Pull Requests.

### Branch Naming Convention

| Prefix | When to use | Example |
|---|---|---|
| `feature/` | New functionality | `feature/badge-qr-generation` |
| `fix/` | Bug fixes | `fix/redeem-duplicate-check` |
| `docs/` | Documentation only | `docs/team-guidelines` |
| `refactor/` | Code restructuring without behavior change | `refactor/auth-blueprint` |
| `chore/` | Dependency updates, config, tooling | `chore/update-pymongo` |

### Creating a branch

Always branch off from the latest `main`:

```bash
git checkout main
git pull origin main
git checkout -b feature/my-feature-name
```

---

## Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/) in English.

### Format

```
<type>: <short imperative description>
```

### Types

| Type | When to use |
|---|---|
| `feat` | Adds a new feature |
| `fix` | Fixes a bug |
| `docs` | Documentation changes only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `chore` | Tooling, dependencies, config — no production code change |
| `test` | Adding or updating tests |
| `style` | Formatting, missing semicolons — no logic change |

### Real examples from this project

```
feat: add QR code generation on badge creation
feat: implement /me/badges endpoint grouped by event
fix: prevent duplicate redemption of the same badge token
fix: return 404 when event id does not exist
docs: add technical documentation and team guidelines
refactor: extract MongoDB connection into db.py module
chore: add Procfile and eventlet for Render deployment
```

### Rules

- Use the **imperative mood**: "add", not "added" or "adds"
- Keep the subject line under 72 characters
- No period at the end of the subject line
- If the change needs more context, add a body after a blank line

---

## Pull Requests

### How to name a PR

Use the same convention as commits — type + short description:

```
feat: add admin dashboard with badge redemption stats
fix: handle expired JWT tokens on /me/badges
docs: add DOCUMENTATION.md and TEAM_RULES.md
```

### What a PR description must include

```
## What this PR does
Brief description of the change and why it's needed.

## How to test
Step-by-step instructions to verify the change works.

## Related issues
Closes #<issue-number> (if applicable)
```

### Who approves

- Every PR requires **at least 1 approval** from another team member before merging.
- The author cannot approve their own PR.
- If the PR touches auth or admin logic, a second review is strongly recommended.

---

## Main Branch Protection

**Never push directly to `main`.** Always open a PR.

```bash
# WRONG — never do this
git push origin main

# CORRECT — push your branch and open a PR
git push origin feature/my-feature-name
```

The `main` branch must always be in a deployable state. Broken code on `main` blocks the entire team.

---

## Resolving Merge Conflicts

1. Pull the latest `main` into your branch before opening a PR:

```bash
git checkout main
git pull origin main
git checkout feature/my-feature-name
git merge main
```

2. Open the conflicting files and resolve manually — do not blindly accept "ours" or "theirs" without reading both sides.

3. After resolving, stage the files and commit:

```bash
git add <resolved-file>
git commit -m "chore: resolve merge conflict with main"
```

4. Push and request a re-review if the PR was already open.

If the conflict is in a critical file (e.g. `db.py`, `__init__.py`, router config), ping the team before resolving — it may need a coordinated decision.
