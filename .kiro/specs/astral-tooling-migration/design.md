# Design Document

## Overview

This design outlines the migration of the Verba project from traditional Python tooling (pip, setuptools, black, mypy) to Astral's modern Python toolchain: uv (package manager), ruff (linter/formatter), and ty (type checker). The migration will modernize the development workflow while maintaining backward compatibility and improving performance.

The current project uses a hybrid approach with both `setup.py` and `pyproject.toml`, along with traditional tools like pip, black, and basic ruff usage. The migration will consolidate configuration, improve performance, and provide a more consistent developer experience.

## Architecture

### Current State Analysis
- **Package Management**: Mixed pip/setuptools with some uv usage in Docker
- **Configuration**: Dual setup.py + pyproject.toml configuration
- **Linting**: Basic ruff + black combination
- **Type Checking**: No systematic type checking in place
- **Build System**: Hatchling build backend
- **Development Workflow**: Make-based with traditional Python tools

### Target State
- **Package Management**: Full uv adoption for all dependency management
- **Configuration**: Consolidated pyproject.toml with comprehensive tool configuration
- **Linting/Formatting**: Ruff as the single tool for linting and formatting
- **Type Checking**: ty for fast, modern type checking
- **Build System**: Maintained hatchling with uv integration
- **Development Workflow**: Updated Make targets using Astral tools

## Components and Interfaces

### 1. Package Management Migration (uv)

**Current Interface:**
```bash
pip install -e ".[dev]"
pip install -r requirements-supabase.txt
python -m venv .venv
```

**Target Interface:**
```bash
uv sync
uv add --dev pytest
uv run verba start
uv venv
```

**Configuration Changes:**
- Migrate from `setup.py` to pure `pyproject.toml`
- Convert `requirements-supabase.txt` to dependency groups
- Update Docker to use uv throughout
- Modify Makefile to use uv commands

### 2. Code Quality Migration (ruff)

**Current Interface:**
```bash
black goldenverba
ruff check goldenverba
```

**Target Interface:**
```bash
ruff format goldenverba
ruff check goldenverba
ruff check --fix goldenverba
```

**Configuration Changes:**
- Remove black dependency and configuration
- Expand ruff configuration in pyproject.toml
- Configure ruff for both linting and formatting
- Update pre-commit hooks and CI/CD

### 3. Type Checking Integration (ty)

**Current Interface:**
- No systematic type checking

**Target Interface:**
```bash
ty check goldenverba
ty check --watch goldenverba
```

**Configuration Changes:**
- Add ty configuration to pyproject.toml
- Configure type checking rules and exclusions
- Integrate with IDE and development workflow

### 4. Build System Updates

**Current Interface:**
- Hatchling build backend
- setup.py for legacy compatibility

**Target Interface:**
- Pure pyproject.toml with hatchling
- uv-compatible build configuration
- Streamlined dependency specification

## Data Models

### pyproject.toml Structure
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
# Core project metadata
name = "goldenverba"
version = "2.0.0"
# ... existing metadata

# Dependency groups for different use cases
[dependency-groups]
dev = ["pytest>=8.0.0", "ruff", "ty"]
test = ["pytest-asyncio", "pytest-cov"]
docs = ["mkdocs", "mkdocs-material"]

[tool.uv]
# uv-specific configuration
dev-dependencies = ["ruff", "ty", "pytest"]

[tool.ruff]
# Comprehensive ruff configuration
line-length = 88
target-version = "py310"

[tool.ruff.lint]
# Linting rules and exclusions

[tool.ruff.format]
# Formatting configuration

[tool.ty]
# Type checking configuration
```

### Makefile Command Mapping
```makefile
# Old commands -> New commands
pip install -e ".[dev]" -> uv sync
black goldenverba -> ruff format goldenverba
ruff check goldenverba -> ruff check goldenverba
# New additions
make typecheck -> uv run ty check goldenverba
```

## Error Handling

### Migration Compatibility
- **Legacy Command Support**: Provide clear error messages for deprecated commands
- **Dependency Conflicts**: Use uv's resolution to handle complex dependency trees
- **Configuration Validation**: Validate pyproject.toml during migration
- **Rollback Strategy**: Maintain backup configurations during transition

### Runtime Error Handling
- **Missing Dependencies**: Clear error messages with uv installation instructions
- **Configuration Errors**: Validate tool configurations with helpful error messages
- **Version Conflicts**: Leverage uv's dependency resolution for conflict resolution

### Development Workflow Errors
- **Tool Not Found**: Check for tool installation and provide installation commands
- **Configuration Issues**: Validate and suggest fixes for common configuration problems
- **Performance Issues**: Monitor and optimize tool performance during migration

## Testing Strategy

### Migration Testing
1. **Dependency Resolution Testing**
   - Verify all dependencies install correctly with uv
   - Test optional dependency groups
   - Validate cross-platform compatibility

2. **Code Quality Testing**
   - Ensure ruff produces equivalent results to black + ruff
   - Verify formatting consistency across codebase
   - Test linting rule coverage and accuracy

3. **Type Checking Testing**
   - Validate ty configuration with existing codebase
   - Test type checking performance and accuracy
   - Ensure IDE integration works correctly

4. **Build System Testing**
   - Verify package builds correctly with new configuration
   - Test installation from built packages
   - Validate entry points and console scripts

### Continuous Integration Updates
- Update GitHub Actions to use uv for dependency management
- Configure ruff for both linting and formatting in CI
- Add ty type checking to CI pipeline
- Ensure Docker builds use optimized uv workflows

### Performance Benchmarking
- Measure dependency installation speed improvements
- Compare linting/formatting performance
- Monitor type checking speed and accuracy
- Track overall development workflow improvements

## Implementation Phases

### Phase 1: Core Migration
- Migrate package management to uv
- Update pyproject.toml configuration
- Remove setup.py and requirements files
- Update basic Makefile commands

### Phase 2: Code Quality Integration
- Configure ruff for comprehensive linting and formatting
- Remove black dependency and configuration
- Update development workflows and documentation

### Phase 3: Type Checking Integration
- Add ty configuration and integration
- Configure type checking rules
- Update IDE and development environment setup

### Phase 4: Optimization and Documentation
- Optimize tool configurations for performance
- Update all documentation and guides
- Finalize CI/CD pipeline updates
- Provide migration guide for team members

## Configuration Examples

### Complete pyproject.toml
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "goldenverba"
version = "2.0.0"
description = "Welcome to Verba: The Golden RAGtriever..."
readme = "README.md"
requires-python = ">=3.10"
license = "BSD-3-Clause"
authors = [
    { name = "Weaviate", email = "edward@weaviate.io" },
]
dependencies = [
    "supabase>=2.10.0",
    "fastapi>=0.115.0",
    # ... all current dependencies
]

[dependency-groups]
dev = [
    "ruff",
    "ty", 
    "pytest>=8.0.0",
    "pytest-cov",
    "pytest-asyncio",
]
google = ["google-genai>=0.8.0"]
huggingface = ["sentence-transformers>=3.3.0"]

[project.scripts]
verba = "goldenverba.server.cli:cli"

[tool.uv]
dev-dependencies = [
    "ruff",
    "ty",
    "pytest>=8.0.0",
]

[tool.ruff]
line-length = 88
target-version = "py310"
src = ["goldenverba"]

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.ty]
files = ["goldenverba"]
python-version = "3.10"
strict = true
```

### Updated Dockerfile
```dockerfile
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variables for uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=/tmp/uv-cache

WORKDIR /Verba

# Copy project files
COPY pyproject.toml ./
COPY README.md ./
COPY goldenverba ./goldenverba

# Install dependencies and the package
RUN uv pip install --system --no-cache -e .

EXPOSE 8000
CMD ["verba", "start", "--host", "0.0.0.0"]
```

This design provides a comprehensive migration path while maintaining the project's functionality and improving the development experience through modern Python tooling.