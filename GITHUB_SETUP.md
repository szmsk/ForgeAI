# GitHub release checklist

This repository is prepared to be pushed as a public GitHub repository.

## 1. Create the repository

Create an empty repository named `forgeai` under the GitHub account `szmsk`.
Do not initialize it with another README, `.gitignore` or license because those files are already included here.

## 2. Initialize and push

From the repository root:

```bash
git init
git branch -M main
git add .
git status
git commit -m "feat: initial ForgeAI multi-tenant platform"
git remote add origin https://github.com/szmsk/forgeai.git
git push -u origin main
```

## 3. Before pushing

Run:

```bash
python scripts/secret_scan.py
cd backend && python -m compileall -q app
```

If dependencies are installed:

```bash
pytest -q
ruff check app tests
```

For the frontend, from `frontend/` run `npm install` once and commit the generated `package-lock.json`. CI will then use the lockfile for reproducible installs if you change the workflow from `npm install` to `npm ci`.

## 4. GitHub repository settings

Recommended public-repository settings:

- enable Dependabot alerts
- enable secret scanning if available on the account/plan
- protect `main`
- require pull-request review for protected branches
- require the CI workflow to pass before merge
- disable force pushes to `main`
- add a repository description and topics

Suggested topics:

`ai-engineering`, `ai-agents`, `llm`, `python`, `fastapi`, `kubernetes`, `multi-tenant`, `devops`, `observability`, `sandbox`, `github-actions`

## 5. First release

After the first successful CI run, create a GitHub release tagged `v2.0.0`.

Do not describe the system as universally production-secure. Use the wording **production-oriented reference implementation** until it has been deployed, load-tested and hardened in a real target environment.
