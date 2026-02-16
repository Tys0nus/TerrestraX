# Contributing to TerrestraX

Thanks for contributing.

## Development setup

1. Install Python 3.10+.
2. Install Webots.
3. Create and activate a virtual environment.
4. Install development tools:

```bash
pip install pre-commit ruff
pre-commit install
```

## Coding conventions

- Follow existing module boundaries in `architecture.md`.
- Prefer `snake_case` for functions and variables.
- Keep changes focused and minimal.
- Do not commit generated artifacts (`__pycache__`, notebook checkpoints, temporary files).

## Commit and PR guidance

- Use clear commit messages.
- Keep pull requests small and reviewable.
- Include a short test/validation note in each PR description.

## Notebooks

- Notebook files are allowed in the repository.
- Strip outputs before committing to keep diffs readable.
