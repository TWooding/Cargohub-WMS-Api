## Contribution Guidelines

### Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification for our commit messages. This means that each commit message should start with a type (e.g., feat, fix, chore) followed by a short description of the change.

## Package Manager

We use [uv](https://docs.astral.sh/uv/getting-started/installation/) as our package manager. To install the dependencies, run:

```bash
uv sync
```

## Tests

De tests draaien op een kopie van de data map, de echte data wordt dus niet aangepast. Run de tests met:

```bash
uv run pytest
```

Tests met `xfail` zijn bekende problemen uit het onderzoeksrapport. De reden staat in de output.
