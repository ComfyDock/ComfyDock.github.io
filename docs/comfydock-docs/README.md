# ComfyDock Documentation

Documentation site for ComfyDock v1.0+ - the package and environment manager for ComfyUI.

## Quick Start

### Install dependencies

```bash
pip install mkdocs-material pymdown-extensions
```

Or with uv:

```bash
uv tool install mkdocs --with mkdocs-material --with pymdown-extensions
```

### Local development

```bash
mkdocs serve
```

Visit `http://localhost:8000` to view the docs.

### Build static site

```bash
mkdocs build
```

Output will be in `site/` directory.

### Deploy to GitHub Pages

```bash
mkdocs gh-deploy
```

## Documentation Structure

```
docs/
├── index.md                          # Landing page
├── getting-started/                  # ✅ Phase 1 Complete
│   ├── installation.md
│   ├── quickstart.md
│   ├── concepts.md
│   └── migrating-from-v0.md
├── user-guide/                       # 🚧 Phase 2 TODO
│   ├── workspaces.md
│   ├── environments/
│   ├── custom-nodes/
│   ├── models/
│   ├── workflows/
│   ├── python-dependencies/
│   └── collaboration/
├── cli-reference/                    # 🚧 Phase 3 TODO
│   ├── global-commands.md
│   ├── environment-commands.md
│   └── ...
├── troubleshooting/                  # 🚧 Phase 4 TODO
│   ├── common-issues.md
│   └── ...
└── legacy/                           # Old v0.x docs (Docker-based)
    └── ...
```

## Status

**Phase 1 (Complete)**: ✅ Getting Started section with 4 comprehensive guides

See `DOCUMENTATION_STATUS.md` for detailed roadmap and progress tracking.

## Writing Guidelines

### Tone

Follow Anthropic Claude Code documentation style:

- Friendly and conversational
- Practical, example-driven
- Progressive disclosure (beginner → advanced)
- Use "you" and "your"
- Clear, actionable instructions

### Structure

Each guide should include:

1. Title + one-line description
2. Prerequisites (if any)
3. Core content with examples
4. Common variations
5. Troubleshooting tips
6. Next steps with links

## Contributing

1. Create new .md file in appropriate section
2. Follow tone and structure guidelines
3. Add to `mkdocs.yml` nav
4. Test locally with `mkdocs serve`
5. Submit PR

See `DOCUMENTATION_STATUS.md` for what needs writing.

## Files of Note

- `mkdocs.yml` - Site configuration and navigation
- `docs/index.md` - Landing page
- `docs/stylesheets/extra.css` - Custom CSS
- `DOCUMENTATION_STATUS.md` - Detailed status and roadmap

## Questions?

- GitHub Issues: https://github.com/ComfyDock/comfydock/issues
- GitHub Discussions: https://github.com/ComfyDock/comfydock/discussions

