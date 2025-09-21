# ComfyDock Workflow Node Resolution Strategy

## Problem Statement

**Challenge**: ComfyUI workflows JSON files contain node types (e.g., `"Depthflow"`, `"NumberRound"`) but don't specify which custom node packages provide those node types. When missing nodes are detected, we need to resolve:
- `node_type` → `package_id` → `download_url`

**Current State**: ComfyUI Manager uses large, manually-maintained reverse lookup tables (`extension-node-map.json`) that require constant synchronization with the rapidly evolving ComfyUI ecosystem.

**Goal**: Eliminate maintenance burden while providing accurate, real-time node resolution for any ComfyUI workflow.

## Analysis: Current ComfyUI Manager Approach

### Architecture Overview
ComfyUI Manager uses a sophisticated multi-layered system:

1. **Registry Database**: `custom-node-list.json` - All available packages with download URLs
2. **Reverse Lookup Table**: `extension-node-map.json` - Maps repository URLs to specific node class names
3. **Multi-Step Detection**: 
   - Parse workflow for node types
   - Compare against registered nodes  
   - Use CNR ID, AUX ID, or raw node type matching
   - Apply regex patterns for dynamic node matching

### Key Limitations
- ❌ **Manual Maintenance**: Requires constant updates to mapping files
- ❌ **Sync Lag**: Mappings become outdated as packages evolve
- ❌ **Scale Issues**: Manual curation doesn't scale to thousands of packages
- ❌ **Single Point of Failure**: Centralized mapping files create bottlenecks

## ComfyUI Registry API Analysis

### Available Endpoints
```bash
# Node Search
GET /nodes/search?search=query&limit=10

# Node Details  
GET /nodes/{nodeId}

# Installation Info
GET /nodes/{nodeId}/install

# ComfyNode Metadata (when available)
GET /nodes/{nodeId}/versions/{version}/comfy-nodes
```

### Key Capabilities
- ✅ **Real-time Search**: Dynamic package discovery
- ✅ **Complete Package Info**: Downloads, dependencies, repository URLs
- ✅ **Version Management**: Access to all package versions
- ✅ **ComfyNode Metadata**: Exact `NODE_CLASS_MAPPINGS` when uploaded

### Critical Limitations
- ❌ **No Reverse Lookup**: Can't search by exact node name
- ❌ **Incomplete Metadata**: Not all packages have ComfyNode metadata
- ❌ **Search-Based Only**: Must guess package names from node types

## Test Cases & Real-World Examples

### Case 1: Depthflow Workflow
**Workflow contains**: `"Depthflow"`, `"DepthflowMotionPresetCircle"`
**Package**: `comfyui-depthflow-nodes` 
**Resolution**: ✅ Search for "depthflow" finds correct package
**Challenge**: ❌ No ComfyNode metadata available (upload timing issue)

### Case 2: Basic Math Nodes  
**Workflow contains**: `"NumberRound"`, `"UnaryMath"`, `"IntegerInput"`
**Package**: `basic-math`
**Resolution**: ❌ Search for "NumberRound" returns no results
**Challenge**: ❌ No way to discover `basic-math` from individual node names

### Case 3: Akatz Custom Nodes
**Workflow contains**: `"AK_AudioreactiveDynamicDilationMask"`
**Package**: `comfyui-akatz-nodes`
**Resolution**: ✅ Has complete ComfyNode metadata
**Success**: ✅ Perfect reverse lookup when metadata exists

## Proposed Solution: Automated Reverse Lookup Table

### Strategy Overview
Build a **comprehensive, automatically-maintained reverse lookup table** using GitHub Actions that scans all registry packages nightly. This approach provides reliability and completeness without depending on incomplete registry API endpoints.

**Key Decision**: We **cannot trust the real-time registry API** until they add an actual reverse lookup endpoint (`GET /nodes/reverse-lookup?node_name=NumberRound`). The search API is too unreliable for exact node name matching.

### Two-Tier Data Collection System

#### Tier 1: ComfyNode Metadata (When Available)
```python
# For packages with uploaded metadata
GET /nodes/{id}/versions/{version}/comfy-nodes
# Returns: {"comfy_node_name": "AK_AudioreactiveDynamicDilationMask", ...}
# Confidence: "exact_metadata"
```

#### Tier 2: Direct Package Inspection (Fallback)
```python
# For packages without metadata - DOWNLOAD AND INSPECT
1. Download package zip from download_url
2. Extract and locate __init__.py
3. Parse NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS
4. Extract all node type names
# Confidence: "source_inspection"
```

### Automated Source Code Analysis
When ComfyNode metadata is missing, the GitHub Action will:

1. **Download Package**: Use `download_url` from registry
2. **Extract Archive**: Handle .zip/.tar.gz formats  
3. **Locate Init File**: Find `__init__.py` or `nodes.py`
4. **Parse Node Mappings**: Extract `NODE_CLASS_MAPPINGS` dictionary
5. **Build Reverse Map**: Create node_name → package_id entries
6. **Cache Results**: Store in lookup table with confidence level

## Implementation Architecture

### GitHub Actions Automation
```yaml
# Runs nightly at 2 AM UTC
- name: Scan Registry for All Packages
  run: python scripts/registry_scanner.py --fetch-all
  
- name: Download Missing Package Sources  
  run: python scripts/source_inspector.py --download-missing
  
- name: Parse Node Mappings from Source Code
  run: python scripts/node_parser.py --parse-init-files
  
- name: Build Comprehensive Reverse Lookup Table
  run: python scripts/mapping_builder.py --merge-all-sources
  
- name: Commit Updated Mappings
  run: git commit -m "🤖 Auto-update node mappings"
```

### Mapping File Format
```json
{
  "schema_version": "1.0.0",
  "last_updated": "2025-09-11T10:30:00Z",
  "total_packages": 1205,
  "total_nodes": 8349,
  "mappings": {
    "NumberRound": [
      {
        "package_id": "basic-math",
        "package_name": "Basic Math Nodes", 
        "version": "1.2.1",
        "confidence": "exact_metadata",
        "github_stars": 145,
        "downloads": 12847,
        "node_count": 23,
        "rank": 1
      },
      {
        "package_id": "comfyui-depthflow-nodes",
        "package_name": "ComfyUI-Depthflow-Nodes",
        "version": "1.2.1", 
        "confidence": "source_inspection",
        "github_stars": 312,
        "downloads": 29390,
        "node_count": 15,
        "rank": 2
      }
    ]
  }
}
```

### Conflict Resolution Algorithm

#### Problem: Multiple Packages Provide Same Node
Example: Both `basic-math` and `advanced-math` provide `NumberRound`

#### Solution: Workflow-Based Coverage Optimization
```python
def resolve_conflicts(workflow_nodes):
    # 1. Calculate coverage: which packages provide most needed nodes
    # 2. Apply tie-breakers: GitHub stars, downloads, node count
    # 3. Select minimal set of packages for maximum coverage
    
    # Example result:
    # basic-math: provides 4/4 workflow nodes ✅ WINNER
    # advanced-math: provides 1/4 workflow nodes ❌ 
```

#### Tie-Breaking Hierarchy
1. **Coverage Percentage** (most important)
2. **GitHub Stars** (community trust)
3. **Downloads** (popularity/stability)
4. **Node Count** (package maturity)
5. **Confidence Level** (exact_metadata > search_based)

### Workflow Resolution Process
```python
# 1. Extract node types from workflow JSON
workflow_nodes = {"Depthflow", "NumberRound", "UnaryMath"}

# 2. Load comprehensive lookup table (local file)
lookup_table = load_mapping_file("node-to-package.json")

# 3. Find exact matches for all workflow nodes
exact_matches = lookup_table.get_matches(workflow_nodes)
# Returns candidates with confidence levels: "exact_metadata" or "source_inspection"

# 4. Apply conflict resolution algorithm
optimal_packages = resolve_conflicts(exact_matches, workflow_nodes)

# 5. Handle any unresolved nodes (should be rare)
if unresolved_nodes:
    log_missing_nodes(unresolved_nodes)  # For future lookup table improvements

# Result: Optimal package selection from comprehensive lookup table
```

## Key Benefits

### Eliminates Maintenance Burden
- ✅ **Automated Updates**: GitHub Actions handle all synchronization
- ✅ **Version Tracking**: Automatically detects new package releases  
- ✅ **No Manual Curation**: Scales to thousands of packages automatically

### Provides Comprehensive Accuracy
- ✅ **Complete Coverage**: Both metadata AND source code inspection
- ✅ **Reliable Resolution**: No dependency on unreliable search APIs
- ✅ **High Confidence**: Clear distinction between metadata vs. source-based matches

### Optimal Package Selection  
- ✅ **Coverage Optimization**: Minimizes number of required packages
- ✅ **Community Validation**: Uses GitHub stars and downloads as signals
- ✅ **Conflict Resolution**: Handles overlapping node names intelligently

### Future-Proof Architecture
- ✅ **Self-Improving**: Automatically gets better as packages add metadata
- ✅ **Source Code Fallback**: Never blocked by missing API features
- ✅ **Extensible**: Easy to add new parsing strategies for different package formats

## Implementation Priority

### Phase 1: Basic Automated Lookup Table
1. **GitHub Actions Setup**: Nightly registry scanning for all packages
2. **ComfyNode Metadata Extraction**: Parse existing registry metadata
3. **Simple Source Code Parser**: Extract NODE_CLASS_MAPPINGS from __init__.py
4. **Basic Mapping File Generation**: Create initial lookup table

### Phase 2: Advanced Source Code Analysis
1. **Robust Archive Handling**: Support .zip, .tar.gz, .tar formats
2. **Smart Init File Discovery**: Handle various package structures
3. **Advanced AST Parsing**: Extract complex mapping patterns
4. **Error Handling**: Graceful failures for unparseable packages

### Phase 3: Comprehensive Conflict Resolution
1. **Workflow-Based Coverage Algorithm**: Optimize package selection
2. **Advanced Tie-Breaking**: Full hierarchy with community signals
3. **Integration with ComfyDock**: Update node resolution system
4. **Performance Optimization**: Efficient local file lookups

## Expected Outcomes

### Short Term (1-2 months)
- ✅ **95%+ Resolution Rate**: Comprehensive coverage via source code inspection
- ✅ **Zero Maintenance**: Fully automated updates eliminate manual work
- ✅ **Instant Lookups**: Local file provides immediate resolution

### Medium Term (3-6 months)  
- ✅ **98%+ Resolution Rate**: Advanced parsing handles edge cases
- ✅ **Optimal Package Selection**: Coverage algorithm minimizes dependencies
- ✅ **Community Adoption**: Other tools adopt our comprehensive mapping files

### Long Term (6+ months)
- ✅ **Industry Standard**: Becomes reference implementation for node resolution
- ✅ **Registry API Improvements**: Our approach influences registry to add reverse lookup
- ✅ **Near Perfect Resolution**: 99%+ accuracy through comprehensive source analysis

## Risk Mitigation

### Source Code Parsing Complexity
- **Mitigation**: AST parsing with fallback to regex pattern matching
- **Error Handling**: Graceful failures log issues for manual review
- **Quality Control**: Confidence levels distinguish parsing reliability

### Package Archive Variations  
- **Mitigation**: Support multiple archive formats (.zip, .tar.gz, .tar)
- **Discovery Logic**: Smart searching for __init__.py in various locations
- **Backup Strategy**: Manual whitelist for problematic packages

### GitHub Actions Resource Limits
- **Mitigation**: Incremental updates, only process changed packages
- **Optimization**: Parallel processing and efficient caching
- **Monitoring**: Alerts for failed runs and resource usage tracking

## Conclusion

This **automated reverse lookup table approach** eliminates the maintenance burden while providing comprehensive accuracy through direct source code inspection. By combining registry metadata extraction with automated package analysis, we create a system that:

1. **Achieves near-complete coverage** by inspecting ALL packages, not just those with metadata
2. **Requires zero maintenance** through fully automated GitHub Actions
3. **Provides reliable resolution** without depending on incomplete registry APIs
4. **Optimizes package selection** through intelligent conflict resolution

The result is a **comprehensive, zero-maintenance node resolution system** that provides superior coverage by directly analyzing package source code when metadata is unavailable. This approach ensures we can resolve even edge cases like your Depthflow nodes that lack ComfyNode metadata.

## Source Code Analysis Details

### Example: Parsing Depthflow Nodes
```python
# Download: comfyui-depthflow-nodes-1.2.1.zip
# Extract and locate: __init__.py
# Parse NODE_CLASS_MAPPINGS:
{
  "Depthflow": Depthflow,
  "DepthflowMotionPresetCircle": DepthflowMotionPresetCircle,
  "DepthflowMotionPresetZoom": DepthflowMotionPresetZoom,
  # ... all 15 nodes
}

# Result: Perfect reverse mapping with "source_inspection" confidence
```

This ensures **no package is left behind** - every package gets analyzed regardless of whether the registry has processed its metadata correctly.


### Side note:
Our local workflow parsing tool needs to know which nodes are ComfyUI-native nodes, and which belong to custom nodes.
As a result we may want to have an additional mapping file called "comfyui-native-nodes-map.json" which contains just this list for multiple versions of ComfyUI (for backwards compatibility).
We can ideally automate this process with a github action to look for new releases and update the mapping with the latest core nodes.