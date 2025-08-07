# Verba Contribution Guidelines

Welcome to the Verba community! We're thrilled that you're interested in contributing to the Verba project. Verba is a collaborative open-source project, and we believe that everyone has something unique to contribute. Below you'll find our guidelines which aim to make contributing to Verba a respectful and pleasant experience for everyone.

## 🌟 Community and Open Source

Open source is at the heart of Verba. We appreciate feedback, ideas, and enhancements from the community. Whether you're looking to fix a bug, add a new feature, or simply improve the documentation, your contribution is important to us.

## 📚 Before You Begin

Before contributing, please take a moment to read through the [README](https://github.com/weaviate/Verba/README.md) and the [Technical Documentation](https://github.com/weaviate/Verba/TECHNICAL.md). These documents provide a comprehensive understanding of the project and are essential reading to ensure that we're all on the same page.

## 🐛 Reporting Issues

If you've identified a bug or have an idea for an enhancement, please begin by creating an Issue. Here's how:

- Check the Issue tracker to ensure the bug or enhancement hasn't already been reported.
- Clearly describe the issue including steps to reproduce when it is a bug.
- Include as much relevant information as possible.

## 💡 Ideas and Feedback

We welcome all ideas and feedback. If you're not ready to open an Issue or if you're just looking for a place to discuss ideas, head over to our [GitHub Discussions](https://github.com/weaviate/Verba/discussions) or the [Weaviate Support Page](https://forum.weaviate.io/).

## 📝 Pull Requests

If you're ready to contribute code or documentation, please submit a Pull Request (PR) to the dev branch. Here's the process:

- Fork the repository and create your branch from `main`.
- Set up your development environment using uv (recommended):
  ```bash
  # Install uv if you haven't already
  curl -LsSf https://astral.sh/uv/install.sh | sh
  
  # Clone and setup
  git clone https://github.com/your-username/Verba.git
  cd Verba
  uv sync --group dev
  ```
- Ensure that your code adheres to the existing code style. We use [ruff](https://docs.astral.sh/ruff/) for both formatting and linting Python code.
- If you're adding a new feature, consider writing unit tests and documenting the feature.
- Verify that your changes pass existing unit tests
- Make sure your code lints, formats, and type checks correctly:
  ```bash
  uv run ruff format goldenverba  # Format code
  uv run ruff check goldenverba   # Lint code
  uv run ty check goldenverba     # Type checking (preview)
  ```
- Include a clear description of your changes in the PR.
- Link to the Issue in your PR description.

### 🧪 Tests and Formatting

To maintain the quality of the codebase, we ask that all contributors:

- **Format your code** with ruff (replaces black):
  ```bash
  uv run ruff format goldenverba
  ```
- **Lint your code** with ruff:
  ```bash
  uv run ruff check goldenverba
  uv run ruff check --fix goldenverba  # Auto-fix issues
  ```
- **Type check your code** with ty (preview tool):
  ```bash
  uv run ty check goldenverba
  ```
  **Note:** ty is currently in preview. If you encounter issues, please report them or temporarily skip type checking.
- **Run unit tests** to ensure that nothing is broken:
  ```bash
  uv run pytest --cov=goldenverba
  ```
- **Or run all checks at once** using the Makefile:
  ```bash
  make check  # Runs format, lint, typecheck, and tests
  make format # Just format code
  make lint   # Just lint code
  make test   # Just run tests
  ```

### Development Workflow

1. **Setup your environment:**
   ```bash
   uv sync --group dev
   ```

2. **Make your changes and test locally:**
   ```bash
   uv run verba start  # Test the application
   ```

3. **Run quality checks:**
   ```bash
   make check  # Or run individual commands above
   ```

4. **Commit and push your changes**

### 🔄 Pull Request Process

- PRs are reviewed on a regular basis.
- Engage in the conversation and make requested updates to your PR if needed.
- Once approved, your PR will be merged into the main branch by a maintainer.

## 🗨️ Stay Connected

We encourage you to join our community channels. Stay connected, share ideas, and get to know fellow contributors.

Thank you for being a part of Verba. Your contributions not only help improve the project but also the wider community of users and developers.

Happy contributing!
