# ComfyDock Model Management Specification
**Version:** 0.1.0 (MVP)  
**Status:** Draft  
**Scope:** Single-developer MVP

## Problem Statement

ComfyUI workflows break when shared between users because model files are referenced by arbitrary local filenames. Users rename models, store them in different locations, and have no reliable way to identify if they already have a required model under a different name.

## Solution Overview

ComfyDock uses content hashing (blake3, sha256) to identify models regardless of filename or location. When sharing workflows, model references are replaced with hashes. When importing workflows, ComfyDock helps users locate required models through multiple resolution strategies.

## MVP Scope

### In Scope
- Scanning local model files and building hash index
- Embedding model metadata in exported workflows
- Resolving models by hash when importing workflows
- Manual model registration and path mapping

### Out of Scope (Post-MVP)
- Automatic model downloading
- Community model registry
- Model version management
- Cloud model storage

## Core Concepts

### Model Identity
Every model file has a unique identity based on its blake3 hash, not its filename. The same model file might be named differently across systems but will have the same hash.

### Model Index
A local database mapping (sqlite) hashes to file paths on the user's system. Built by scanning model directories and updated when models are added/moved.

### Model Hints
Metadata embedded in workflows that helps locate models, including original filenames, known sources, and size information.

## User Workflows

### Workflow 1: First-Time Setup
```
User installs ComfyDock
→ User runs: comfydock model scan
→ System scans common model locations
→ System builds local hash index
→ User sees summary of indexed models
```

### Workflow 2: Exporting a Workflow
```
User creates workflow in ComfyUI
→ User runs: comfydock workflow export my-workflow
→ System reads workflow file
→ System replaces model names with hashes
→ System embeds model hints (size, original names)
→ System saves enhanced workflow file
```

### Workflow 3: Importing a Workflow
```
User receives workflow from another user
→ User runs: comfydock workflow import shared-workflow
→ System extracts required model hashes
→ For each model:
  - If hash exists in local index → Link to local file
  - If hash not found → Show model info and ask user to locate
→ System updates workflow with local paths
→ User can run workflow in ComfyUI
```

### Workflow 4: Manual Model Registration
```
User downloads new model manually
→ User runs: comfydock model register ~/downloads/new-model.safetensors
→ System calculates hash
→ System adds to index
→ System links to ComfyUI models folder (optional)
```

## Command Reference

### Model Discovery Commands
```bash
# Scan for models in standard locations
comfydock model scan

# Scan specific directory
comfydock model scan --path /my/models

# Show indexed models
comfydock model list

# Search for specific model
comfydock model search <query>
```

### Model Registration Commands
```bash
# Register a single model
comfydock model register <path>

# Show model details
comfydock model info <hash-prefix>

# Find model by hash
comfydock model locate <hash-prefix>
```

### Workflow Commands
```bash
# Export workflow with model metadata
comfydock workflow export <workflow-file>

# Import workflow and resolve models
comfydock workflow import <workflow-file>

# Check if workflow can run (all models available)
comfydock workflow check <workflow-file>
```

## Model Resolution Strategy

When importing a workflow, ComfyDock attempts to resolve each model hash in order:

1. **Local Index Check**  
   Search local hash index for exact match

2. **Filename Hint**  
   If model not found by hash, search by original filename (with user confirmation)

3. **Manual Location**  
   Prompt user to locate model file manually

4. **Skip Model**  
   Allow user to skip (workflow may fail in ComfyUI)

## Data Storage

### Model Index Format
The model index stores:
- Hash (blake3, sha256)
- Current file path
- File size
- Last seen timestamp
- Original filename (if known)

### Workflow Metadata Format
Enhanced workflows include:
- Original workflow JSON
- Model mapping (name → hash)
- Model hints per hash (size, possible sources, original names)

## User Messages

### Success Messages
- "Indexed 24 models in 3 directories"
- "Workflow exported with 3 model references"
- "All models resolved successfully"

### Warning Messages
- "Model not found: <hash> (original name: SD15.ckpt, size: 4.2GB)"
- "Multiple models match filename hint, please select"
- "Some models could not be resolved, workflow may not run correctly"

### Error Messages
- "Cannot read workflow file: <path>"
- "Model file not accessible: <path>"
- "No models found in scanned directories"

## MVP Limitations

1. **No Automatic Downloads** - Users must manually download missing models
2. **No Version Tracking** - Only tracks current hash, not model versions
3. **Local Only** - No sharing of model indexes between users
4. **No Deduplication** - Duplicate model files counted separately

## Success Metrics

- User can export and import workflows between their own environments
- Model resolution success rate > 80% for workflows with common models
- Model scanning completes in < 30 seconds for typical collections

## Future Enhancements (Post-MVP)

- Integration with CivitAI API for hash-based lookups
- Community model registry for hash → source mappings
- Automatic model downloading with user consent
- Model deduplication and space optimization
- Integration with HuggingFace model hub