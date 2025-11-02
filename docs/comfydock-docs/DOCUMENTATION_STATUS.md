# ComfyDock Documentation Status

## Overview

This document tracks the status of the ComfyDock v1.0 documentation rewrite. The documentation has been reorganized to reflect the new UV-based architecture and follows an Anthropic-style tone similar to Claude Code docs.

## Completed (Phase 1)

### Core Structure

- ✅ Moved legacy v0.x docs to `docs/legacy/`
- ✅ Created new directory structure for v1.0 docs
- ✅ Updated `mkdocs.yml` with new navigation
- ✅ Added Material for MkDocs theme with modern features
- ✅ Created custom CSS (`stylesheets/extra.css`)

### Getting Started Section (Complete)

- ✅ `index.md` - Main landing page with Anthropic-style overview
- ✅ `getting-started/installation.md` - Complete installation guide
- ✅ `getting-started/quickstart.md` - 5-minute quickstart tutorial
- ✅ `getting-started/concepts.md` - Deep dive into core concepts
- ✅ `getting-started/migrating-from-v0.md` - Migration guide for v0.x users

### Key Features

**Documentation Style:**

- Anthropic Claude Code tone (friendly, practical, actionable)
- Progressive disclosure (beginner → advanced)
- Heavy use of code examples and command outputs
- Admonitions (tips, notes, warnings) for important context
- Tab-based code blocks for platform differences

**Navigation:**

- Sticky tabs for main sections
- Expandable sidebar navigation
- Search with smart highlighting
- Dark/light theme toggle
- Footer navigation

## In Progress / TODO

### Phase 2: Core User Guide

These sections are referenced in the nav but need content:

**User Guide - Workspaces:**
- [ ] `user-guide/workspaces.md` - Workspace management, configuration

**User Guide - Environments:**
- [ ] `user-guide/environments/creating-environments.md` - Detailed environment creation
- [ ] `user-guide/environments/running-comfyui.md` - Running, stopping, managing
- [ ] `user-guide/environments/version-control.md` - Commit, rollback, commit log

**User Guide - Custom Nodes:**
- [ ] `user-guide/custom-nodes/adding-nodes.md` - Registry, GitHub, local dev
- [ ] `user-guide/custom-nodes/managing-nodes.md` - Update, remove, list
- [ ] `user-guide/custom-nodes/node-conflicts.md` - Resolving dependency conflicts

**User Guide - Models:**
- [ ] `user-guide/models/model-index.md` - How model indexing works
- [ ] `user-guide/models/downloading-models.md` - CivitAI, HuggingFace, direct URLs
- [ ] `user-guide/models/managing-models.md` - Index commands (list, find, show, sync)
- [ ] `user-guide/models/adding-sources.md` - Adding download URLs to models

**User Guide - Workflows:**
- [ ] `user-guide/workflows/workflow-resolution.md` - Resolving dependencies
- [ ] `user-guide/workflows/workflow-tracking.md` - How workflows are tracked

**User Guide - Python Dependencies:**
- [ ] `user-guide/python-dependencies/py-commands.md` - py add/remove/list
- [ ] `user-guide/python-dependencies/constraints.md` - Managing constraints

**User Guide - Collaboration:**
- [ ] `user-guide/collaboration/export-import.md` - Tarball export/import
- [ ] `user-guide/collaboration/git-remotes.md` - Remote add/remove/list, push, pull
- [ ] `user-guide/collaboration/team-workflows.md` - Best practices for teams

### Phase 3: CLI Reference

Complete command reference pages:

- [ ] `cli-reference/global-commands.md` - init, list, import, export, model, registry
- [ ] `cli-reference/environment-commands.md` - create, use, delete, run, status, repair
- [ ] `cli-reference/node-commands.md` - node add/remove/list/update
- [ ] `cli-reference/workflow-commands.md` - workflow list/resolve
- [ ] `cli-reference/model-commands.md` - model download/index/add-source
- [ ] `cli-reference/shell-completion.md` - Completion install/uninstall/status

### Phase 4: Troubleshooting

- [ ] `troubleshooting/common-issues.md` - FAQ-style solutions
- [ ] `troubleshooting/dependency-conflicts.md` - Resolving node conflicts
- [ ] `troubleshooting/missing-models.md` - Model resolution issues
- [ ] `troubleshooting/uv-errors.md` - UV command failures
- [ ] `troubleshooting/environment-corruption.md` - Repair, cleanup

### Phase 5: Advanced Topics

Future sections (not in current nav):

- [ ] Advanced torch backend configuration
- [ ] Development node workflows
- [ ] Registry cache management
- [ ] CivitAI API configuration
- [ ] Workspace advanced configuration

## Content Guidelines

### Tone & Style (Anthropic-inspired)

**DO:**
- Use friendly, conversational tone
- Start with practical examples
- Include real command outputs
- Use "you" and "your" (not "the user")
- Show before/after states
- Provide "Next steps" at the end
- Use admonitions for tips and warnings

**DON'T:**
- Be overly formal or academic
- Include backwards compatibility notes
- Over-explain every detail
- Add unnecessary fallbacks
- Create complex abstractions

### Structure Pattern

Each guide page should follow:

1. **Title + tagline** - One-sentence description
2. **Prerequisites** (if any)
3. **Core content** - Step-by-step with examples
4. **Common variations** - "What if I want to..."
5. **Troubleshooting** - Quick fixes for common issues
6. **Next steps** - Links to related guides

### Code Example Pattern

```markdown
## Adding a custom node

Add a node from the ComfyUI registry:

\`\`\`bash
cfd node add comfyui-manager
\`\`\`

**Output:**

\`\`\`
🔍 Looking up node: comfyui-manager
✓ Found in registry: ltdrdata/ComfyUI-Manager
📦 Installing dependencies...
✓ Node installed: comfyui-manager
\`\`\`

!!! tip "Add from GitHub"
    \`\`\`bash
    cfd node add https://github.com/ltdrdata/ComfyUI-Manager
    \`\`\`
```

## Building the Docs

### Install dependencies

```bash
cd docs/comfydock-docs
pip install mkdocs-material mkdocs-git-revision-date-localized-plugin
```

### Local development

```bash
mkdocs serve
# Visit http://localhost:8000
```

### Build static site

```bash
mkdocs build
# Output in site/
```

### Deploy to GitHub Pages

```bash
mkdocs gh-deploy
```

## Migration Notes

### From v0.x docs

The old Docker-based documentation has been moved to `docs/legacy/` and is still accessible via the "Legacy Docs (v0.x)" section in the nav. This allows v0.x users to reference old docs while transitioning.

**Key differences:**

| Aspect | v0.x Docs | v1.0 Docs |
|--------|-----------|-----------|
| Architecture | Docker + GUI | UV + CLI |
| Commands | `comfydock` | `cfd` |
| Focus | Environment cards, mount configs | Commands, git workflow |
| Examples | Screenshots, videos | Terminal commands, output |

## Assets & Media

### TODO: Add media

- [ ] Landing page demo GIF/asciinema
- [ ] Update logo/favicon for v1.0 branding
- [ ] Screenshots for key workflows (optional)

### Current assets

- Logo: `assets/comfy_env_manager-min.png` (reused from v0.x)
- CNAME: Points to custom domain (if configured)

## Review Checklist

Before marking Phase 1 complete:

- [x] All getting-started pages complete and proofread
- [x] mkdocs.yml navigation structure correct
- [x] Legacy docs moved and linked
- [x] Custom CSS working
- [x] Code examples tested
- [x] Links between pages working
- [ ] Spell check all content
- [ ] Technical review by maintainer

## Contributing

When adding new documentation:

1. Follow the structure pattern above
2. Use Anthropic tone guidelines
3. Include practical examples
4. Test all command examples
5. Add to appropriate section in mkdocs.yml
6. Cross-link related pages

## Questions / Decisions Needed

1. **Video/GIFs**: Should we add terminal recordings (asciinema)? If yes, which sections?
2. **API Docs**: Should we auto-generate API docs for core library?
3. **Versioning**: Use mike for version-specific docs?
4. **Translations**: Plan for internationalization?
5. **Search**: Add algolia or stick with built-in?

## Timeline Estimate

- **Phase 1 (Complete)**: ~4 hours ✅
- **Phase 2**: ~8-10 hours (user guide sections)
- **Phase 3**: ~4-6 hours (CLI reference)
- **Phase 4**: ~3-4 hours (troubleshooting)
- **Phase 5**: ~2-3 hours (advanced topics)

**Total remaining**: ~20-25 hours of writing

## Contact

For questions about documentation:

- GitHub Issues: https://github.com/ComfyDock/comfydock/issues
- GitHub Discussions: https://github.com/ComfyDock/comfydock/discussions
