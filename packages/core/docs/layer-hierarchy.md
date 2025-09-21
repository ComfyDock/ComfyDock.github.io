cli/          (top level, depends on core/)

  factories/    (can import from core/ to help instantiate objects)
  core/         (orchestrates everything, "Public API")
  *Note: "can import" order: WorkspaceFactory -> Workspace -> EnvironmentFactory -> Environment*

    managers/     (depends on lower layers)

      services/     (depends on models/, utils/)
        ├── github_client.py
        ├── registry_client.py
        └── node_registry.py

      integrations/ (depends on all lower layers)
        └── uv_command.py

        logging/      (only depends on models/)
        utils/        (only depends on models/)

          models/       (no dependencies on other layers)
            ├── types.py      (basic types)
            ├── protocols.py  (interface definitions)
            └── exceptions.py