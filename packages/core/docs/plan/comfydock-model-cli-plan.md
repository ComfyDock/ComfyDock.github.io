# Simplified Model Command Structure
bash# Directory Management
comfydock model dir add <path> [--no-scan]     # Add AND scan by default
comfydock model dir remove <path>
comfydock model dir list

## Update Operations
comfydock model sync                            # Update all tracked dirs
comfydock model sync <path>                     # Update specific dir

## Query Operations  
comfydock model status                          # Overview + stale warnings
comfydock model list                            # List indexed models
comfydock model find <query>                    # Search by name/hash
Key Behaviors
model dir add - Does Everything Initially
bash$ comfydock model dir add ~/external/models
🔍 Scanning ~/external/models...
✓ Found 156 models (42 checkpoints, 89 loras, 25 vae)
✓ Added to tracked directories
✓ Indexed in 12.3 seconds
The --no-scan flag would be rare - only for adding a directory you'll scan later.
model sync - Smart Updates Only
bash$ comfydock model sync
🔄 Checking tracked directories...
  ~/ComfyUI/models: No changes (skipped)
  ~/external/models: 3 new, 2 modified, 1 removed
✓ Index updated in 2.1 seconds
Implementation Strategy
pythonclass ModelDirectoryManager:
    def add_directory(self, path: Path, scan: bool = True):
        """Add directory to tracking and optionally scan."""
        # 1. Add to workspace config
        self.workspace.add_model_directory(path)
        
        # 2. Scan immediately by default
        if scan:
            scanner = ModelScanner()
            models = scanner.scan_directory(path)
            self.index.add_models(models)
    
    def sync_directories(self, path: Path | None = None):
        """Smart sync - only process changes."""
        dirs_to_sync = [path] if path else self.workspace.get_tracked_dirs()
        
        for dir_path in dirs_to_sync:
            # Quick mtime check first
            if not self._has_changes(dir_path):
                continue
                
            # Only scan changed files
            changes = self._detect_changes(dir_path)
            self._apply_changes(changes)
Why This is Better

Clearer mental model: "add" includes initial scan, "sync" updates later
No redundant commands: Each command has a distinct purpose
Progressive complexity: Basic users just use add, never need sync
Efficient by default: sync only processes changes

Additional Simplifications
Consider removing these from MVP:

Labels for directories (just use the path)
Primary/secondary directories (handle this in download logic)
Staleness warnings (users sync when they need to)

Keep the focus on:

Track directories
Build/update index
Find models by hash

This gives you the minimum viable model system that actually works, without overengineering the CLI.

# Model file integrity checks (on sync):
Modification Time Approach
Speed: ~1-10ms per file

Single stat() system call per file
Only reads filesystem metadata (inode)
No disk I/O for file contents
Benefits from OS filesystem cache

For 1000 model files: ~1-10 seconds total
Hash Approach (even "short" hashes)
Speed: ~50-500ms per file (for large models)

Must open and read file contents
Disk I/O bottleneck (even if reading just 1MB for a "quick hash")
CPU time for hash calculation
Can't leverage filesystem metadata cache

For 1000 model files: ~1-10 minutes total
Hybrid Strategy for Your Use Case
pythonclass ModelIndexManager:
    def quick_validate(self, model_dir: Path) -> ValidationResult:
        """Fast validation using mtime + size."""
        changes = []
        
        for file_path in model_dir.glob("**/*"):
            if not self._is_model_file(file_path):
                continue
                
            stat = file_path.stat()
            cached = self.get_cached_stat(file_path)
            
            if not cached:
                changes.append(('new', file_path))
            elif (stat.st_mtime != cached.mtime or 
                  stat.st_size != cached.size):
                changes.append(('modified', file_path))
                
        return ValidationResult(is_valid=len(changes)==0, changes=changes)
    
    def deep_validate(self, file_path: Path) -> bool:
        """Expensive validation using hash (only for changed files)."""
        # Only hash files that failed quick validation
        return calculate_blake3(file_path) == self.get_cached_hash(file_path)
Recommended Approach

Store both mtime AND hash in your index:

sqlCREATE TABLE model_index (
    path TEXT PRIMARY KEY,
    blake3_hash TEXT NOT NULL,
    file_size INTEGER,
    mtime REAL,  -- Store this for quick checks
    last_validated TIMESTAMP
);

Use two-tier validation:

Quick scan (daily/on startup): Check mtime + size
Deep scan (on-demand/suspicious changes): Rehash changed files


Smart invalidation:

pythondef validate_models(self, quick_only=True):
    """Validate model index."""
    # First pass: quick mtime check
    potentially_changed = self.quick_validate(self.models_dir)
    
    if not quick_only and potentially_changed:
        # Second pass: hash only the changed files
        for change_type, path in potentially_changed:
            if change_type == 'modified':
                if self.deep_validate(path):
                    # File mtime changed but content same (touch, copy, etc)
                    self.update_mtime(path)
                else:
                    # Content actually changed
                    self.reindex_model(path)
Important Caveats
mtime is not foolproof:

Can be preserved during copies (cp -p)
Can be manually modified (touch -t)
Some sync tools preserve mtime
Different granularity on different filesystems (FAT32: 2 seconds, ext4: nanoseconds)

But for your use case it's probably fine because:

Model files are rarely modified after download
Users typically add/remove models, not modify them
You can do deep validation when users explicitly request it
The performance gain is worth the small accuracy tradeoff

For a pre-customer MVP with large model files, I'd definitely use the mtime approach for routine checks and save full hashing for when you actually need certainty (like before sharing/exporting).