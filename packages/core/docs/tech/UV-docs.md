# UV Package Manager: Essential Commands & Configuration

UV is a fast, Rust-based Python package manager that replaces pip, virtualenv, pipx, and other tools with a unified CLI. It's 10-100x faster than pip with universal lockfiles for reproducible environments.

## Core Commands

### Project Management
- `uv init [project-name]` - Initialize project with pyproject.toml and .venv
- `uv add <package>` - Add dependency, updates pyproject.toml and uv.lock
- `uv remove <package>` - Remove dependency, updates files
- `uv lock` - Generate/update universal lockfile (uv.lock)
- `uv sync` - Install dependencies from lockfile
- `uv run <command>` - Execute in project environment (auto-syncs)
- `uv build` - Build distributions (wheels/source)
- `uv publish` - Upload to PyPI

### Script Execution
- `uv run script.py` - Run script with inline dependencies (PEP 723)
- `uv run --with rich script.py` - Add dependencies for single run
- `uvx <tool>` - Run tools in ephemeral environments (like pipx)

### Tool Management
- `uv tool install <tool>` - Install tools globally
- `uv tool upgrade <tool>` - Upgrade (respects version constraints)

### Python Versions
- `uv python install 3.11` - Install Python versions
- `uv python pin 3.11` - Pin version via .python-version
- `uv venv` - Create virtual environment

### pip Compatibility
- `uv pip install <package>` - Drop-in pip replacement
- `uv pip compile requirements.in` - Like pip-tools (use --universal)
- `uv pip sync requirements.txt` - Install from lockfile

## Key Differences from pip

- **Virtual environments by default** - No accidental global installs
- **Security-first index strategy** - Prevents dependency confusion attacks
- **Stricter pre-release handling** - Use `--prerelease allow` if needed
- **No --user flag** - Use virtual environments instead
- **Universal lockfiles** - Single uv.lock works across platforms
- **PEP 517 build isolation** - Use `--no-build-isolation` for problematic packages

## Essential Environment Variables

### Most Commonly Used
- `UV_CACHE_DIR` - Override cache location
- `UV_COMPILE_BYTECODE=1` - Compile .pyc files for faster startup
- `UV_OFFLINE=1` - Disable network access
- `UV_NO_PROGRESS=1` - Disable progress bars (CI/CD)
- `UV_LOCKED=1` - Assert lockfile unchanged (CI/CD)
- `UV_PYTHON` - Force specific Python interpreter
- `UV_INDEX` - Additional package indexes (space-separated)
- `UV_DEFAULT_INDEX` - Override default PyPI index

### Standard Variables (inherited)
- `VIRTUAL_ENV` - Detect active environment
- `HTTP_PROXY`, `HTTPS_PROXY` - Network proxy settings
- `NO_COLOR` - Disable colored output
- `RUST_LOG` - Control uv's verbose logging

## Resolution Strategies

- `--resolution latest` (default) - Latest compatible versions
- `--resolution lowest` - Minimum versions (good for library testing)
- `--resolution lowest-direct` - Min direct deps, latest transitive

## Best Practices

1. **Use pyproject.toml** - Declarative dependency management
2. **Commit uv.lock** - Ensures reproducible builds
3. **Use uvx for tools** - Ephemeral, isolated tool execution
4. **Set UV_COMPILE_BYTECODE=1** - For production deployments
5. **Use --universal flag** - For cross-platform lockfiles
6. **Leverage --exclude-newer** - For reproducible historical builds

## pip → uv Command Map

| pip/virtualenv | uv equivalent | Notes |
|---|---|---|
| `python -m venv .venv` | `uv venv` | Much faster |
| `pip install pkg` | `uv add pkg` | Updates pyproject.toml + lockfile |
| `pip install -r req.txt` | `uv pip sync req.txt` | Ensures exact match |
| `pip uninstall pkg` | `uv remove pkg` | Updates project files |
| `pip-compile` | `uv pip compile --universal` | Cross-platform by default |
| `pipx run tool` | `uvx tool` | Cached ephemeral environments |
| `pipx install tool` | `uv tool install tool` | Global tool installation |
| `pyenv install 3.11` | `uv python install 3.11` | Integrated Python management |

## Configuration

Create `uv.toml` in project root for persistent settings:

```toml
[tool.uv]
index-url = "https://private-index.com/simple/"
extra-index-url = ["https://pypi.org/simple/"]
```

UV provides a unified, fast, and secure Python environment management solution with excellent reproducibility guarantees through universal lockfiles.