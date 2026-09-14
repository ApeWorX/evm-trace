# Development

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then create the development environment with Python 3.10 or newer:

```bash
# clone the github repo and navigate into the folder
git clone https://github.com/ApeWorX/evm-trace.git
cd evm-trace

# install the project in editable mode and all development dependency groups
uv sync --group dev
```

Run the same checks as CI:

```bash
uv run --no-sync pytest
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy .
uv run --no-sync mdformat --check README.md CONTRIBUTING.md tests/data/geth/historical_delegatecalls.md
uv build
```

The `style`, `lint`, and `test` dependency groups also support smaller environments for individual CI jobs. They are development groups, not installable package extras. `uv.lock` is local and ignored; run `uv sync --upgrade --group dev` to refresh dependencies when needed.

## Pre-Commit Hooks

We use [`pre-commit`](https://pre-commit.com/) hooks to simplify linting and ensure consistent formatting among contributors.
Use of `pre-commit` is not a requirement, but is highly recommended.

Install `pre-commit` locally from the root folder:

```bash
uv run --no-sync pre-commit install --hook-type pre-commit --hook-type commit-msg
```

Committing will now automatically run the local hooks and ensure that your commit passes all lint checks.
Ruff, mypy, and mdformat hooks use the tools from the uv development environment, so they share the project's dependency constraints and installed dependencies. After changing dependency groups, run `uv sync --group dev` before committing.

## Pull Requests

Pull requests are welcomed! Please adhere to the following:

- Ensure your pull request passes our linting checks
- Include test cases for any new functionality
- Include any relevant documentation updates

It's a good idea to make pull requests early on.
A pull request represents the start of a discussion, and doesn't necessarily need to be the final, finished submission.

If you are opening a work-in-progress pull request to verify that it passes CI tests, please consider
[marking it as a draft](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-requests#draft-pull-requests).

Join the ApeWorX [Discord](https://discord.gg/apeworx) if you have any questions.
