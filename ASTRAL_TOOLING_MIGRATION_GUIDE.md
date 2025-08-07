# Astral Tooling Migration Guide

This guide helps developers transition from traditional Python tooling to Astral's modern Python toolchain: **uv** (package manager), **ruff** (linter/formatter), and **ty** (type checker).

## 🚀 Quick Start

### For New Contributors

If you're new to the project, simply follow the updated setup instructions:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup the project
git clone https://github.com/weaviate/Verba.git
cd Verba
uv sync --group dev
uv run verba start
```

### For Existing Contributors

If you have an existing development environment, follow the migration steps below.

## 📋 Migration Steps

### Step 1: Install uv

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

### Step 2: Clean Up Old Environment (Optional but Recommended)

```bash
# Remove old virtual environment
rm -rf .venv

# Remove old dependency files (already migrated to pyproject.toml)
# These files have been removed: setup.py, requirements-supabase.txt, goldenverba/requirements.txt
```

### Step 3: Setup New Environment

```bash
# Create new environment and install dependencies
uv sync --group dev

# Verify installation
uv run verba --help
```

### Step 4: Update Your Workflow

Replace your old commands with new ones:

| Old Command | New Command |
|-------------|-------------|
| `pip install -e ".[dev]"` | `uv sync --group dev` |
| `black goldenverba` | `uv run ruff format goldenverba` |
| `ruff check goldenverba` | `uv run ruff check goldenverba` |
| `pytest --cov=goldenverba` | `uv run pytest --cov=goldenverba` |
| N/A | `uv run ty check goldenverba` (new!) |

## 🛠️ Tool Comparison

### Package Management: pip → uv

**Before (pip):**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**After (uv):**
```bash
uv sync --group dev
uv run verba start
```

**Benefits:**
- 10-100x faster dependency resolution
- Built-in virtual environment management
- Lockfile support for reproducible builds
- Better dependency conflict resolution

### Code Formatting: black → ruff

**Before (black):**
```bash
black goldenverba
```

**After (ruff):**
```bash
uv run ruff format goldenverba
```

**Benefits:**
- 10-100x faster formatting
- Compatible with black formatting
- Integrated with linting
- More configuration options

### Linting: Multiple tools → ruff

**Before (multiple tools):**
```bash
ruff check goldenverba
flake8 goldenverba
isort goldenverba
```

**After (ruff only):**
```bash
uv run ruff check goldenverba
uv run ruff check --fix goldenverba  # Auto-fix issues
```

**Benefits:**
- Single tool for all linting needs
- Faster execution
- Better error messages
- Auto-fix capabilities

### Type Checking: None → ty

**Before:**
- No systematic type checking

**After:**
```bash
uv run ty check goldenverba
```

**Benefits:**
- Extremely fast type checking (Rust-powered)
- Better error messages than traditional tools
- Incremental checking
- Easy configuration

**Note:** ty is currently in preview (version 1a17) but we're using it to stay on the cutting edge of Astral's toolchain. It's stable enough for development use and will become production-ready soon.

## 🔧 Development Workflow

### Daily Development

```bash
# Start development
uv run verba start

# Run tests
uv run pytest

# Format and lint code
uv run ruff format goldenverba
uv run ruff check goldenverba

# Type checking
uv run ty check goldenverba

# Run all checks
make check
```

### Adding Dependencies

```bash
# Add a new dependency
uv add requests

# Add a development dependency
uv add --group dev pytest-mock

# Add an optional dependency group
uv add --group google google-genai
```

### Docker Development

The Docker setup has been optimized for uv:

```bash
# Build with optimized caching
docker compose build

# Run with new configuration
docker compose up -d
```

## 🚨 Troubleshooting

### Common Issues

#### 1. "uv: command not found"

**Solution:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart your shell or source the profile
source ~/.bashrc  # or ~/.zshrc
```

#### 2. "No such file or directory: setup.py"

**Solution:** This is expected! `setup.py` has been replaced by `pyproject.toml`. Use `uv sync` instead of `pip install -e .`

#### 3. "Module not found" errors

**Solution:**
```bash
# Ensure all dependencies are installed
uv sync --group dev --group test

# Check if you're in the right directory
uv run python -c "import goldenverba; print('OK')"
```

#### 4. "ruff: command not found"

**Solution:**
```bash
# Install development dependencies
uv sync --group dev

# Run ruff through uv
uv run ruff --version
```

#### 5. Type checking errors with ty

**Solution:**
```bash
# ty is in preview, so some errors are expected
# You can run ty with verbose output to see more details
uv run ty check goldenverba --verbose

# If ty crashes or has issues, you can temporarily skip type checking
# or fall back to mypy if needed:
# uv add --group dev mypy
# uv run mypy goldenverba --ignore-missing-imports
```

**Note:** Since ty is in preview (version 1a17), you may encounter:
- Occasional crashes or unexpected behavior
- Missing features compared to mypy/pyright
- False positives or negatives in type checking

This is expected and will improve as ty matures.

### Performance Issues

If you experience slow performance:

1. **Clear uv cache:**
   ```bash
   uv cache clean
   ```

2. **Update uv:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Check disk space:**
   ```bash
   df -h
   ```

## 🔄 Rollback Procedures

If you need to rollback to the old tooling:

### Emergency Rollback

```bash
# 1. Create traditional virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install from PyPI
pip install goldenverba

# 3. Or install from source (if you have the old setup.py)
# Note: setup.py has been removed, so you'll need to restore it from git history
git show HEAD~1:setup.py > setup.py
pip install -e .

# 4. Install development tools
pip install black ruff pytest pytest-cov
```

### Partial Rollback

You can use traditional tools alongside uv:

```bash
# Use pip in uv environment
uv run pip install some-package

# Use black instead of ruff format
uv run black goldenverba

# Use traditional pytest
uv run python -m pytest
```

## 📚 Additional Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [ruff Documentation](https://docs.astral.sh/ruff/)
- [ty Documentation](https://docs.astral.sh/ty/)
- [Migration Design Document](.kiro/specs/astral-tooling-migration/design.md)
- [Project Requirements](.kiro/specs/astral-tooling-migration/requirements.md)

## 🆘 Getting Help

If you encounter issues not covered in this guide:

1. Check the [GitHub Issues](https://github.com/weaviate/Verba/issues)
2. Ask in [GitHub Discussions](https://github.com/weaviate/Verba/discussions)
3. Consult the [Weaviate Support Page](https://forum.weaviate.io/)

## ✅ Migration Checklist

- [ ] Install uv
- [ ] Remove old virtual environment
- [ ] Run `uv sync --group dev`
- [ ] Test that `uv run verba start` works
- [ ] Update your IDE/editor configuration
- [ ] Update any local scripts or aliases
- [ ] Verify CI/CD pipelines work (if you contribute to CI)
- [ ] Update team documentation (if applicable)

---

**Migration completed successfully!** 🎉

You're now using Astral's modern Python toolchain for faster, more reliable development.
