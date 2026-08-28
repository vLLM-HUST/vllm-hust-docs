# Repository and Integration Lifecycle

Status: **normative draft**

## 1. Lifecycle classes

| Class | Meaning | Required controls |
|---|---|---|
| `core` | Organization-owned contract or required default implementation | named maintainers, compatibility policy, release gate, regression tests |
| `supported` | Maintained component or platform profile | compatibility matrix, installation path, behavior tests, known limitations |
| `certified_external` | External project treated as a first-class integration | upstream owner, tested versions, conformance tests, security and fallback notes |
| `incubating` | HUST research or integration being stabilized | sponsor, graduation criteria, experimental label, no default enablement |
| `community` | Useful integration without organization support commitment | owner and scope displayed; excluded from release gate |
| `deprecated` | Replacement exists and removal is scheduled | migration guide, deadline, rollback window |
| `archived` | No active development | read-only repository, final status, successor link if any |

## 2. Four ways to absorb a system

“Absorb” does not imply forking. A system enters the ecosystem through one of
four modes:

1. `core_owned`: vLLM-HUST owns the stable contract and default behavior;
2. `hust_owned_subsystem`: HUST owns and releases an independent subsystem;
3. `certified_external_integration`: HUST owns compatibility and evidence but
   not the external project's source;
4. `experimental_adapter`: the adapter is discoverable but carries no support
   promise.

Mooncake and LMCache normally use mode 3. PegaFlow uses mode 2 while it is
incubating. LMCache-Ascend is a platform provider that may graduate from mode 4
to mode 3 after its compatibility and hardware evidence gates are satisfied.

## 3. Required repository metadata

Each active repository MUST declare:

- canonical repository role and contained artifacts;
- ownership and named maintainers;
- upstream relationship and synchronization policy;
- lifecycle class and maturity;
- supported release or compatibility matrix;
- validation commands and evidence location;
- successor or migration target when deprecated.

Repository metadata MUST agree with the ecosystem registry. The registry wins
for public classification; the component repository wins for implementation
details and test commands.

The organization maintains two deliberately separate inventories:

- `registry/ecosystem-components.json` classifies deployable systems, runtime
  components, bridges, tools, and public applications;
- `registry/repository-portfolio.json` classifies source repositories and their
  relationship to the runtime.

A repository is a source and governance boundary, not a runtime type. A single
repository may contain an external service, several connectors, and packaging;
conversely, one ecosystem system may span more than one repository. Repository
presence alone MUST NOT imply plugin compatibility or support status.

## 4. Incubation graduation

An incubating component graduates to `supported` only when it has:

1. a typed integration contract owned outside the component implementation;
2. no required private monkey patch without an approved removal plan;
3. named maintainers and a release process;
4. behavior tests for startup, steady state, failure, recovery, and shutdown;
5. a compatibility matrix covering core, platform, and hardware stack;
6. hardware correctness evidence when device behavior is claimed;
7. reproducible provenance for every public performance claim;
8. documented rollback and disablement.

## 5. Fork policy

Fork an external project only when all of these conditions hold:

- a long-lived hardware or deployment delta cannot be upstreamed promptly;
- a maintainer accepts responsibility for upstream synchronization;
- a drift budget and synchronization automation exist;
- real-hardware correctness and performance gates exist;
- the user value exceeds the additional release and security burden.

Otherwise, maintain an adapter, compatibility profile, and conformance suite
against the upstream project.

## 6. Cross-repository release train

A supported release record contains exact identifiers for:

- runtime core;
- platform profile;
- extension or connector distribution;
- external subsystem;
- hardware software stack;
- conformance result;
- benchmark run and workload specification;
- known limitations and rollback target.

The public website consumes this record. It does not infer compatibility from
repository presence or import success.
