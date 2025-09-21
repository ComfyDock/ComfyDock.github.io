● Architecture Options Analysis

  Looking at your data pipeline, you have a clear three-stage process with
  distinct storage needs. Let me analyze the best approaches:

  Current Data Flow

  Registry API → Cache (32MB) → Mappings (8MB) → + Manager (1.2MB) → Final
  (11MB)

  Recommended Approach: Hybrid Data Repository

  Structure

  # comfydock-registry-data/ (separate public repo)
  cache/
    registry_cache.json         # Latest cache (32MB)
    registry_cache.json.sha256  # Checksum for validation
    metadata.json              # Build metadata (date, stats)
  history/
    2025/09/
      registry_cache_20250919.json.gz  # Historical snapshots
  manager/
    extension-node-map.json    # Mirror of Manager data
    last_updated.txt          # Track freshness

  # comfydock/ (main repo)  
  src/comfydock_core/data/
    node_mappings.json        # Only this (11MB)
  scripts/
    update_registry.sh        # Local update script
  .github/workflows/
    update_mappings.yml       # Nightly automation

  Why This Works Best

  Benefits:
  1. Clean separation - Users only download what they need (11MB)
  2. Version history - Full git history of cache changes in data repo
  3. Community resource - Public data repo can help other projects
  4. Efficient updates - GitHub Actions can shallow clone data repo
  5. Resilient - Cache corrupted? Roll back via git
  6. Transparent - Anyone can see how mappings evolve

  Implementation Flow:
  graph LR
      A[Nightly Action] --> B[Clone data repo]
      B --> C[Fetch Registry updates]
      C --> D[Update cache]
      D --> E[Fetch Manager data]
      E --> F[Build mappings]
      F --> G[Commit cache to data repo]
      F --> H[Commit mappings to main repo]

  GitHub Actions Workflow

  name: Update Node Mappings
  on:
    schedule:
      - cron: '0 2 * * *'  # 2 AM UTC daily
    workflow_dispatch:      # Manual trigger

  jobs:
    update-mappings:
      runs-on: ubuntu-latest
      steps:
        # 1. Setup
        - uses: actions/checkout@v4
          with:
            token: ${{ secrets.COMFYDOCK_TOKEN }}

        # 2. Clone data repo
        - name: Clone data repository
          run: |
            git clone https://github.com/YOUR_ORG/comfydock-registry-data.git 
  data

        # 3. Update registry cache
        - name: Update Registry Cache
          run: |
            uv run scripts/build_registry_cache.py \
              --input data/cache/registry_cache.json \
              --output data/cache/registry_cache.json \
              --checkpoint-interval 50

        # 4. Update Manager extension data
        - name: Fetch Manager Data
          run: |
            curl -L https://raw.githubusercontent.com/ltdrdata/ComfyUI-Manager
  /main/extension-node-map.json \
              > data/manager/extension-node-map.json

        # 5. Build final mappings
        - name: Generate Mappings
          run: |
            # Build from cache
            uv run scripts/build_global_mappings.py \
              --cache data/cache/registry_cache.json \
              --output temp_mappings.json

            # Augment with Manager
            uv run scripts/augment_mappings.py \
              --mappings temp_mappings.json \
              --manager data/manager/extension-node-map.json \
              --output src/comfydock_core/data/node_mappings.json

        # 6. Commit to data repo
        - name: Update data repository
          run: |
            cd data
            if [[ -n $(git status -s) ]]; then
              git config user.name "GitHub Actions"
              git config user.email "actions@github.com"
              git add .
              git commit -m "Update registry cache - $(date -I)"
              git push https://${{ secrets.DATA_REPO_TOKEN 
  }}@github.com/YOUR_ORG/comfydock-registry-data.git
            fi

        # 7. Commit to main repo
        - name: Commit mapping changes
          run: |
            if [[ -n $(git diff --name-only 
  src/comfydock_core/data/node_mappings.json) ]]; then
              git add src/comfydock_core/data/node_mappings.json
              git commit -m "Update node mappings - $(date -I)"
              git push
            fi

  Alternative: GitHub Releases (Simpler)

  If you prefer a single-repo solution:

  # After building cache, create release
  - name: Create Release with Cache
    uses: softprops/action-gh-release@v1
    with:
      tag_name: cache-${{ github.run_number }}
      files: |
        registry_cache.json.gz
        build_metadata.json
      body: "Registry cache snapshot"

  Then download in future runs:
  - name: Download latest cache
    run: |
      LATEST=$(gh release list --limit 1 --exclude-drafts | grep cache- | cut 
  -f1)
      gh release download $LATEST --pattern "registry_cache.json.gz"
      gunzip registry_cache.json.gz

  Why NOT These Options

  External Database: Overkill for 32MB, adds complexity and potential costs

  Git LFS: Adds complexity, not needed for files under 100MB

  S3/R2: External dependency, though R2's free tier would work well

  Actions Artifacts: Only 90-day retention, not suitable for long-term storage

  Migration Path

  1. Create comfydock-registry-data repo
  2. Initial population with current cache
  3. Set up GitHub Actions secrets
  4. Test workflow manually
  5. Enable nightly schedule

  This approach gives you version control, automation, and keeps your main
  repo lean while maintaining full transparency and reproducibility.