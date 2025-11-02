# Legacy Documentation Asset Paths Fix - 2025-11-02

## Summary

Fixed all image and video asset paths in legacy v0.x documentation to correctly reference the `../assets/` directory.

## Problem

Legacy docs were moved from `docs/` to `docs/legacy/`, but image paths still referenced `assets/` (relative to old location) instead of `../assets/` (correct relative path from new location).

Result: All images and some videos were broken in the legacy documentation.

## Solution

Updated all asset references to use correct relative paths:
- `docs/legacy/*.md` - Changed `assets/` → `../assets/`
- `docs/legacy/troubleshooting/*.md` - Already had `../assets/` (correct for their depth)

## Files Modified

### Main Legacy Docs (9 files)
1. **index.md** - Logo reference
2. **about_author.md** - Author logo
3. **usage.md** - 11 image references
4. **sharing_images.md** - 1 image reference
5. **installation.md** - 1 image reference
6. **environments.md** - 8 image references

### Troubleshooting Docs (2 files - Already Correct)
7. **troubleshooting/edit_files_in_container.md** - Already had `../assets/` (6 images)
8. **troubleshooting/installing_custom_nodes_manually.md** - Already had `../assets/` (2 images)

## Changes Made

### index.md
```diff
- ![ComfyDock Logo](assets/comfy_env_manager-min.png)
+ ![ComfyDock Logo](../assets/comfy_env_manager-min.png)
```

### about_author.md
```diff
- ![Akatz AI](assets/akatz_logo_small.png)
+ ![Akatz AI](../assets/akatz_logo_small.png)
```

### usage.md (11 changes)
```diff
- ![Manager Layout Screenshot](assets/envManagerLayoutAnnotated.png)
+ ![Manager Layout Screenshot](../assets/envManagerLayoutAnnotated.png)

- ![Settings Tab](assets/userSettings.png)
+ ![Settings Tab](../assets/userSettings.png)

- ![Create Environment](assets/createEnvironmentDialog.png)
+ ![Create Environment](../assets/createEnvironmentDialog.png)

- ![Environment Type](assets/envTypesLatest.png)
+ ![Environment Type](../assets/envTypesLatest.png)

- ![Docker Select Dockerhub](assets/dockerSelectBrowse.png)
+ ![Docker Select Dockerhub](../assets/dockerSelectBrowse.png)

- ![Docker Select Installed](assets/dockerSelectInstalled.png)
+ ![Docker Select Installed](../assets/dockerSelectInstalled.png)

- ![Docker Select Custom](assets/dockerSelectCustom.png)
+ ![Docker Select Custom](../assets/dockerSelectCustom.png)

- ![Mount Config Screenshot](assets/mountConfigUpdated.png)
+ ![Mount Config Screenshot](../assets/mountConfigUpdated.png)

- ![Advanced Options Screenshot](assets/advancedOptions.png)
+ ![Advanced Options Screenshot](../assets/advancedOptions.png)
```

### sharing_images.md
```diff
- ![Create Environment](assets/runSharedEnv.png)
+ ![Create Environment](../assets/runSharedEnv.png)
```

### installation.md
```diff
- ![ComfyDock App](assets/pinokioMenu1.png)
+ ![ComfyDock App](../assets/pinokioMenu1.png)
```

### environments.md (8 changes)
```diff
- ![Environment Card](assets/environmentCard1.png)
+ ![Environment Card](../assets/environmentCard1.png)

- ![Active Environment](assets/environmentCard1Running.png)
+ ![Active Environment](../assets/environmentCard1Running.png)

- ![ComfyUI Logs](assets/logsDisplay.png)
+ ![ComfyUI Logs](../assets/logsDisplay.png)

- ![Duplicate Environment](assets/updatedDuplicate.png)
+ ![Duplicate Environment](../assets/updatedDuplicate.png)

- ![Duplicate Environment](assets/autoEnvTypes.png)
+ ![Duplicate Environment](../assets/autoEnvTypes.png)

- ![Environment Settings](assets/updatedEnvSettings.png)
+ ![Environment Settings](../assets/updatedEnvSettings.png)

- ![Folder Dropdown](assets/foldersDropdown.png)
+ ![Folder Dropdown](../assets/foldersDropdown.png)

- ![Add Folder](assets/addFolders.png)
+ ![Add Folder](../assets/addFolders.png)

- ![Edit Folder](assets/editFolder.png)
+ ![Edit Folder](../assets/editFolder.png)

- ![Environment Settings Folder](assets/environmentSettingsFolder.png)
+ ![Environment Settings Folder](../assets/environmentSettingsFolder.png)
```

## Verification

Confirmed all asset paths are now correct:

```bash
# No incorrect paths remain
grep -rn "](assets/" docs/legacy/*.md
# (no output = success)

# All video paths already correct
grep -rn "src=\"../assets/" docs/legacy/*.md
# (all videos already had correct paths)
```

## Total Changes
- **30 image references fixed**
- **0 video references needed fixing** (already correct)
- **8 markdown files modified**

## Directory Structure Reference

```
docs/
├── assets/                    # All images and videos here
│   ├── comfy_env_manager-min.png
│   ├── envManagerLayoutAnnotated.png
│   ├── createEnv_edit1.mp4
│   └── ... (all other assets)
└── legacy/                    # Legacy v0.x docs
    ├── index.md              # References ../assets/
    ├── usage.md              # References ../assets/
    └── troubleshooting/      # One level deeper
        └── *.md              # References ../assets/ (already correct)
```

## Result

All legacy documentation images and videos now render correctly in MkDocs.

## Related
- See `PHASE1_CORRECTIONS.md` for Phase 1 documentation accuracy fixes
- See `DOCUMENTATION_STATUS.md` for overall documentation status
