# Release: parentY items to test-parentY (fabric-cicd)

`azure-pipelines.yml` deploys the items committed in the `parentY` folder (the Git folder of the parentY workspace) to the **test-parentY** workspace with [fabric-cicd](https://github.com/microsoft/fabric-cicd).

- **Trigger:** push a tag that points to a commit on `main`, for example:
  ```bash
  git tag v1.0.0 && git push origin v1.0.0
  ```
  Tags on other branches fail the "Verify tag is on main" step.
- **Bulk publish:** Lakehouse, VariableLibrary, Notebook and SemanticModel are published with the bulk import API (experimental `enable_bulk_publish` flag).
- **Standard publish for PaginatedReport:** bulk import does not yet support service principals for paginated reports (`PrincipalTypeNotSupported`), so `deploy.py` publishes them in a second, standard pass. This is a temporary workaround only; once bulk import supports service principals for paginated reports, the second pass can be removed. `$items.SemanticModel.sm_demo.$id` still resolves because the model was deployed in the first pass.
- **Dynamic parameterization:** `parameter.yml` has no hard-coded IDs. Each `find_value` is a dynamic variable that resolves the value in the source workspace (`$workspace.parentY...`), and each `replace_value` resolves the value in the target workspace.

| Item | What is re-pointed | find_value (source) | replace_value (target) |
|------|--------------------|---------------------|------------------------|
| `nb_demo` | Default lakehouse | `$workspace.parentY.$items.Lakehouse.lh_demo.$id` | `$items.Lakehouse.lh_demo.$id` |
| `nb_demo` | Default lakehouse workspace | `$workspace.parentY.$id` | `$workspace.$id` |
| `sm_demo` | Direct Lake SQL endpoint | `$workspace.parentY.$items.Lakehouse.lh_demo.$sqlendpoint` | `$items.Lakehouse.lh_demo.$sqlendpoint` |
| `sm_demo` | Direct Lake SQL endpoint id | `$workspace.parentY.$items.Lakehouse.lh_demo.$sqlendpointid` | `$items.Lakehouse.lh_demo.$sqlendpointid` |
| `rpt_demo` | Data source semantic model | `$workspace.parentY.$items.SemanticModel.sm_demo.$id` | `$items.SemanticModel.sm_demo.$id` |
| `vl_demo` | `workspace_name` variable | `$.variables[?(@.name=="workspace_name")].value` | `$workspace.$name` |

Pipeline variables: `TENANT_ID`, `CLIENT_ID`, and secret `CLIENT_SECRET`. The service principal needs access to both parentY (to resolve source values) and test-parentY.

After deployment, run `nb_demo` in test-parentY to load `dbo.sales`, then refresh `sm_demo` so `rpt_demo` shows data.
