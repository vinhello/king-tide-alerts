# Branching Strategy

## Branch types
| Branch | Pattern | Purpose |
|---|---|---|
| Production | `main` | Always deployable — deploys to Railway automatically |
| Features | `feature/short-description` | New functionality |
| Fixes | `fix/short-description` | Bug fixes |
| Chores | `chore/short-description` | Dependencies, config, docs |

There is no `develop` branch. Railway deploys directly from `main`.

## Rules
1. **Never commit directly to `main`** (enforced by pre-commit hook)
2. Branch from `main` for all work
3. PR targets `main`
4. Delete branches after merge

## Commit format
Use conventional commits (enforced by commit-msg hook):
```
feat: add tide prediction caching
fix: resolve NOAA API timeout handling
chore: update Python dependencies
docs: add API documentation
test: add notification service tests
refactor: extract email template builder
```

Optional scope in parentheses:
```
feat(frontend): add tide chart zoom controls
fix(backend): handle empty NOAA response
```

## PR checklist
- [ ] Branch name follows pattern (`feature/`, `fix/`, `chore/`)
- [ ] PR title is descriptive
- [ ] Tests passing: `cd backend && pytest tests/ -v` and `cd frontend && npx vitest run`
- [ ] Linters passing: `cd backend && ruff check .` and `cd frontend && npm run lint`
- [ ] PR description explains what changed, why, and how to test
