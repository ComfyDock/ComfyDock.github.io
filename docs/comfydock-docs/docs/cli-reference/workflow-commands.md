# Workflow Commands

> Commands for managing and resolving workflow dependencies.


## `workflow`

**Usage:**

```bash
cfd workflow [-h] {list,resolve,model} ...
```

### Subcommands


### `list`

**Usage:**

```bash
cfd workflow list [-h]
```


### `resolve`

**Usage:**

```bash
cfd workflow resolve [-h] [--auto] [--install] [--no-install] name
```

**Arguments:**

- `name` - Workflow name to resolve

**Options:**

- `--auto` - Auto-resolve without interaction (default: `False`)
- `--install` - Auto-install missing nodes without prompting (default: `False`)
- `--no-install` - Skip node installation prompt (default: `False`)


### `model`

**Usage:**

```bash
cfd workflow model [-h] {importance} ...
```

#### Subcommands


#### `importance`

**Usage:**

```bash
cfd workflow model importance [-h]
                                     [workflow_name] [model_identifier]
                                     [{required,flexible,optional}]
```

**Arguments:**

- `workflow_name` - Workflow name (interactive if omitted) (optional)
- `model_identifier` - Model filename or hash (interactive if omitted) (optional)
- `importance` - Importance level (optional)
