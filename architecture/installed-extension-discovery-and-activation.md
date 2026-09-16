# Installed Extension Discovery and Activation

Status: normative Extension Bundle v1 delivery profile.

## 1. Decision

`pip` or `uv pip` installation registers Bundle availability. It does not
activate runtime behavior. Operators enable exact Bundle IDs at fresh process
startup:

```bash
uv pip install vllm-hust
uv pip install example-performance-plugin

vllm plugin inspect org.example.performance
vllm plugin validate org.example.performance
vllm serve MODEL --extension org.example.performance
```

This is the supported simplification. Unconditional “installed means enabled”
is prohibited for scheduler, KV, platform, operator, model-runner, control, and
device-path components. Those components can conflict, require permissions,
change request results, or fail in different owning processes.

## 2. Static registration format

A distribution declares an entry point whose name is the exact Bundle ID and
whose value is a module directory rather than a callable:

```toml
[project.entry-points."vllm.extension_bundles"]
"org.example.performance" = "example_plugin.manifests"

[tool.setuptools.package-data]
example_plugin = ["manifests/vllm-hust-extension-v1.json"]
```

The registered directory contains exactly one supported manifest filename:

- `vllm-hust-extension-v1.json`, preferred for new packages;
- `extension-bundle-v1.json`, retained for existing Bundle v1 packages.

The entry-point name MUST equal the manifest `bundle_id`. The value MUST be a
plain Python module path with no attribute, extras, URL, or filesystem path.

## 3. Discovery boundary

The host reads `importlib.metadata` identities but MUST NOT call
`EntryPoint.load()` during discovery. For an ordinary wheel it locates the
manifest through the exact path recorded in wheel `RECORD` metadata. For a PEP
660 editable install it may read a local-file `direct_url.json` and check only
the project root and its conventional `src/` directory.

Discovery never recursively searches the filesystem, imports a parent package,
executes an editable finder, follows manifest symlinks, performs a network
lookup, or launches a sidecar. An implementation is imported only later by the
owning domain materializer after static admission succeeds.

## 4. Selection and precedence

Selection is ordered and explicit:

```bash
vllm serve MODEL \
  --extension org.example.telemetry \
  --extension org.example.scheduler
```

`--extension` is equivalent to the ordered
`VLLM_EXTENSION_BUNDLES` selection. Child processes inherit that exact
selection. `VLLM_EXTENSION_MANIFESTS` remains available for development and
deployment-pinned files. When an explicitly configured manifest supplies a
selected ID, it takes precedence over an installed registration for that ID.

An unset selection preserves the existing behavior: explicitly configured
manifests are admitted, and installed distributions are not inspected. An empty
selection validates explicit manifests but enables none.

## 5. Failure policy

The following conditions fail startup before implementation import:

- an unknown or empty selected ID;
- duplicate selected IDs;
- multiple distributions registering one selected ID;
- an entry-point name/manifest ID mismatch;
- an invalid entry-point value or missing/duplicated manifest file;
- malformed schema or incompatible host API range;
- unsupported isolation or denied permissions;
- duplicate explicit Bundle IDs;
- domain ambiguity, import, type, factory, or protocol failure after admission.

An invalid unselected installed registration does not affect startup. This is
necessary so an unrelated package cannot break a no-plugin service merely by
being present in the environment. `vllm plugin list` intentionally audits all
registrations and therefore reports any invalid installed registration.

## 6. Operator interface

The read-only commands are:

```bash
vllm plugin list
vllm plugin list --json
vllm plugin inspect BUNDLE_ID
vllm plugin validate BUNDLE_ID \
  --allow-permission network_egress
```

`list` and `inspect` parse only static metadata. `validate` additionally applies
host API, isolation, and permission admission. None of them imports an
implementation module.

The serve command performs early argument extraction before the serving stack
is imported. It writes the ordered selection into the inherited environment so
API, scheduler, engine-core, and worker processes construct the same immutable
snapshot.

## 7. Permissions and auto-activation

Installed metadata cannot grant authority. Non-empty component permissions are
denied unless the operator supplies the exact
`VLLM_EXTENSION_ALLOWED_PERMISSIONS` allowlist. These declarations remain audit
inputs rather than an operating-system sandbox.

Bundle v1 does not currently define `auto_safe`. Even a stat logger can create
cardinality, availability, or data-egress failures. A future auto-activation
profile would require a separate schema identity, a closed list of composable
contracts, zero ambient capability requests, bounded resource behavior, and an
explicit host policy. It MUST NOT be inferred from package installation.

## 8. Packaging and compatibility gates

Every Bundle distribution MUST prove:

1. source and wheel builds contain the registered manifest;
2. the static entry point survives normal and editable installation;
3. discovery does not add the implementation module to `sys.modules`;
4. installed ID, manifest ID, distribution identity, and version are reported;
5. no-selection startup performs no installed scan;
6. exact selection works through CLI and environment forms;
7. duplicate, malformed, incompatible, and permission-denied cases fail closed;
8. each selected domain materializes in its owning process only;
9. dual-published typed and legacy paths preserve domain composition policy;
10. disabling selection and starting a new process restores the documented
    legacy or baseline path.

Behavior, failure recovery, shutdown, correctness, accelerator, and performance
equivalence remain separate domain gates. Successful installation or static
validation is not performance evidence.
