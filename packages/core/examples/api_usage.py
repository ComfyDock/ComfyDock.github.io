"""Example of using the refactored WorkflowManager API from different clients."""

# =============================================================================
# Web API Example (FastAPI)
# =============================================================================

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

@app.get("/workflow/{name}/analyze")
async def analyze_workflow(name: str):
    """Analyze a workflow and return dependency information."""
    try:
        analysis = env.analyze_workflow(name)

        return {
            "name": analysis.name,
            "already_tracked": analysis.already_tracked,
            "missing_packages": [
                {
                    "id": pkg.package_id,
                    "name": pkg.display_name,
                    "suggested_version": pkg.suggested_version,
                    "github_url": pkg.github_url
                }
                for pkg in analysis.missing_packages
            ],
            "installed_packages": [
                {
                    "id": pkg.package_id,
                    "name": pkg.display_name,
                    "version": pkg.installed_version,
                    "version_mismatch": pkg.version_mismatch
                }
                for pkg in analysis.installed_packages
            ],
            "unresolved_nodes": analysis.unresolved_nodes,
            "has_missing": analysis.has_missing_dependencies
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


class TrackRequest(BaseModel):
    install_nodes: List[str] = []


@app.post("/workflow/{name}/track")
async def track_workflow(name: str, request: TrackRequest):
    """Track a workflow with optional node installation."""
    try:
        # Analyze first
        analysis = env.analyze_workflow(name)

        # Install requested nodes
        installed = []
        failed = []
        for node_id in request.install_nodes:
            try:
                env.add_node(node_id, no_test=True)
                installed.append(node_id)
            except Exception as e:
                failed.append({"node": node_id, "error": str(e)})

        # Track the workflow
        env.track_workflow(name, analysis)

        return {
            "status": "tracked",
            "workflow": name,
            "installed_nodes": installed,
            "failed_nodes": failed
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# GUI Application Example (PyQt/Tkinter)
# =============================================================================

class WorkflowTrackingDialog:
    """Example GUI dialog for tracking workflows."""

    def __init__(self, env, workflow_name):
        self.env = env
        self.workflow_name = workflow_name
        self.analysis = None
        self.selected_packages = []

    def analyze(self):
        """Analyze the workflow and populate UI."""
        self.analysis = self.env.analyze_workflow(self.workflow_name)

        # Update UI elements
        self.update_installed_list(self.analysis.installed_packages)
        self.update_missing_list(self.analysis.missing_packages)
        self.update_unresolved_list(self.analysis.unresolved_nodes)

        # Enable/disable buttons based on state
        self.track_button.setEnabled(not self.analysis.already_tracked)
        self.install_button.setEnabled(bool(self.analysis.missing_packages))

    def on_install_clicked(self):
        """Handle install button click."""
        # Show package selection dialog
        dialog = PackageSelectionDialog(self.analysis.missing_packages)
        if dialog.exec():
            self.selected_packages = dialog.get_selected()

            # Install in background
            for pkg in self.selected_packages:
                identifier = pkg.github_url or pkg.package_id
                try:
                    self.env.add_node(identifier, no_test=True)
                    self.show_success(f"Installed {pkg.display_name}")
                except Exception as e:
                    self.show_error(f"Failed to install {pkg.display_name}: {e}")

    def on_track_clicked(self):
        """Handle track button click."""
        try:
            self.env.track_workflow(self.workflow_name, self.analysis)
            self.show_success(f"Started tracking {self.workflow_name}")
            self.close()
        except Exception as e:
            self.show_error(f"Failed to track workflow: {e}")


# =============================================================================
# Jupyter Notebook Example
# =============================================================================

def analyze_and_install_workflow(env, workflow_name, auto_install=False):
    """Interactive workflow analysis for Jupyter notebooks."""
    from IPython.display import display, HTML
    import pandas as pd

    # Analyze workflow
    analysis = env.analyze_workflow(workflow_name)

    # Display results as tables
    if analysis.installed_packages:
        installed_df = pd.DataFrame([
            {
                'Package': pkg.display_name or pkg.package_id,
                'Installed': pkg.installed_version,
                'Suggested': pkg.suggested_version or 'N/A',
                'Match': '✅' if not pkg.version_mismatch else '⚠️'
            }
            for pkg in analysis.installed_packages
        ])
        display(HTML("<h3>Installed Packages</h3>"))
        display(installed_df)

    if analysis.missing_packages:
        missing_df = pd.DataFrame([
            {
                'Package': pkg.display_name or pkg.package_id,
                'Version': pkg.suggested_version,
                'Source': 'GitHub' if pkg.github_url else 'Registry'
            }
            for pkg in analysis.missing_packages
        ])
        display(HTML("<h3>Missing Packages</h3>"))
        display(missing_df)

        if auto_install:
            print("\n🔧 Auto-installing missing packages...")
            for pkg in analysis.missing_packages:
                identifier = pkg.github_url or pkg.package_id
                try:
                    env.add_node(identifier, no_test=True)
                    print(f"✅ {pkg.display_name}")
                except Exception as e:
                    print(f"❌ {pkg.display_name}: {e}")

    # Track workflow
    if not analysis.already_tracked:
        env.track_workflow(workflow_name, analysis)
        print(f"\n✅ Workflow '{workflow_name}' is now tracked")

    return analysis


# =============================================================================
# Programmatic Script Example
# =============================================================================

def batch_process_workflows(env, install_strategy="conservative"):
    """Process multiple workflows programmatically."""
    results = {
        "processed": [],
        "failed": [],
        "skipped": []
    }

    workflows = env.scan_workflows()
    untracked = [name for name, info in workflows.items()
                 if info.state == "watched"]

    for workflow_name in untracked:
        try:
            # Analyze
            analysis = env.analyze_workflow(workflow_name)

            # Decide what to install based on strategy
            if install_strategy == "all":
                # Install everything
                to_install = analysis.missing_packages
            elif install_strategy == "conservative":
                # Only install if fully resolvable
                to_install = analysis.missing_packages if analysis.is_fully_resolvable else []
            else:  # skip
                to_install = []

            # Install nodes
            for pkg in to_install:
                identifier = pkg.github_url or pkg.package_id
                env.add_node(identifier, no_test=True)

            # Track workflow
            env.track_workflow(workflow_name, analysis)

            results["processed"].append({
                "workflow": workflow_name,
                "installed": len(to_install),
                "unresolved": len(analysis.unresolved_nodes)
            })

        except Exception as e:
            results["failed"].append({
                "workflow": workflow_name,
                "error": str(e)
            })

    return results