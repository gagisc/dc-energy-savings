# Contributing to dc-thermal-fusion

Thank you for your interest in contributing! This guide covers the local dev
setup, CI/CD pipeline, and contribution workflow.

---

## Local development setup

```bash
git clone https://github.com/gagisc/dc-thermal-fusion
cd dc-thermal-fusion
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install pre-commit
pre-commit install          # install git hooks
cp .env.example .env        # fill in your device credentials (never commit .env)
```

---

## Branch strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code — protected, requires PR + CI green |
| `develop` | Integration branch for feature merges |
| `feature/<name>` | New features |
| `fix/<name>` | Bug fixes |
| `hotfix/<name>` | Urgent production fixes |

---

## CI/CD pipeline overview

```
PR opened / push to feature branch
  │
  ├─ lint (ruff)            ← runs on every push, fastest feedback
  ├─ typecheck (mypy)       ← parallel with lint
  ├─ security (bandit)      ← parallel with lint
  │
  ├─ test (pytest, py3.11 + py3.12)
  │
  ├─ smoke experiment       ← CPU-only, < 60 s, uploads CSV + PNG artefacts
  │
  └─ docker-build (build check only, no push)

Merge to main
  │
  ├─ All CI jobs above (repeat)
  ├─ docker (build + push to GHCR as :latest + :sha)
  ├─ trivy-scan (container vulnerability scan → SARIF upload)
  └─ integration-smoke (pulls image, runs experiment)

Push tag v*.*.*
  │
  └─ release (GitHub Release + source tarball + smoke artefacts)

Nightly (03:00 UTC)
  └─ nightly benchmark (500 steps, 90-day artefact retention)
```

---

## Running CI locally

```bash
# Lint
ruff check src/ experiments/ --fix
ruff format src/ experiments/

# Type-check
mypy src/ --ignore-missing-imports

# Security
bandit -r src/ -ll

# Tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Smoke experiment
python experiments/run_smoke.py
```

---

## Required secrets (set in GitHub repo settings)

| Secret | Purpose |
|--------|---------|
| `GITHUB_TOKEN` | Auto-provided — used for GHCR push and releases |

No additional secrets are required for CI/CD in simulation mode.
For production device access, add credentials as repo secrets and reference
them in `.env` inside your deployment environment. **Never commit `.env`.**

---

## Pull Request checklist

- [ ] `pre-commit run --all-files` passes with no errors
- [ ] `pytest tests/` passes with ≥ 50 % coverage
- [ ] `python experiments/run_smoke.py` completes without errors
- [ ] No placeholder credentials (`PLACEHOLDER`) in committed files
- [ ] CASE_STUDY.md updated if intervention metrics changed
- [ ] README reproduce command still works end-to-end

---

## Security

Found a vulnerability? Please open a **private security advisory** at
`https://github.com/gagisc/dc-thermal-fusion/security/advisories/new`
rather than a public issue. We aim to respond within 48 hours.
