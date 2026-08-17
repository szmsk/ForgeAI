# Contributing

Thanks for taking an interest in ForgeAI.

## Development setup

```bash
git clone https://github.com/szmsk/forgeai.git
cd forgeai
docker compose up --build
```

For backend-only development:

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
ruff check app tests
```

## Pull requests

Keep changes focused. For agent behavior changes, add or update deterministic tests where possible and document any new security boundary or operational requirement.

Do not commit secrets, generated credentials, local databases, `.env` files or private repository contents.

## Commit style

Prefer conventional prefixes such as:

- `feat:`
- `fix:`
- `test:`
- `docs:`
- `refactor:`
- `security:`
- `chore:`
