# Structured discovery tool schemas

All tools run headlessly in Blender and return JSON.

| Name | Purpose | Output | Failure conditions |
|---|---|---|---|
| `list_armatures` | Enumerate armatures | names, bone count, visibility, active state | invalid file/Blender failure |
| `list_bones` | Describe hierarchy | IDs, parent/children, deform flag, constraint count | invalid armature data |
| `list_shape_keys` | Summarize keys | values, ranges, mute/driver state by object | malformed mesh data |
| `list_drivers` | Describe drivers | owner, path, expression, variables and targets | deleted targets remain null |
| `list_constraints` | Normalize constraints | owner, type, influence, target and limits | malformed constraint data |
| `list_vertex_groups` | Enumerate groups | mesh, name and index; no weight dump | malformed mesh data |
| `get_shape_key_info` | Inspect one key | candidate details and compact delta summary | missing name returns `[]` |
| `get_driver_info` | Find a driver | candidates by ID, path, or key name | missing name returns `[]` |
| `get_constraint_info` | Find a constraint | candidates; optional owner disambiguates | missing name returns `[]` |
| `get_control_dependencies` | Build graph edges | bone/property → driver → key; group → mesh | missing references are nullable |

Example:

```json
{"success":true,"result":[{"source_type":"bone","source":"jawOpen","relationship":"feeds","target_type":"driver","target":"FaceMesh:key_blocks[\"jawOpen\"].value:0:2","deterministic":true}]}
```

Host failures return `success: false`, `error_type`, `message`, and `recoverable`. Empty optional
components are valid and do not crash inventory construction.
