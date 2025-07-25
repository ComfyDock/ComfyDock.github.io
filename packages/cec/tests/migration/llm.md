# Have some way to specify output location like:
# OUTPUT:
# {working_dir}/tests-llm-context.md

INCLUDE:
scripts/migration_tests/
test-automation-plan.md
run_migration_tests.sh

EXCLUDE:
*.pyc
**llm-context.md
**llm.md
CLAUDE.md
uv.lock
.claude
test_results/
env/
comfyui_repos/
scripts/
.venv
.github