# Release: sales-analytics items to test-sales-analytics and prod-sales-analytics (fabric-cicd)

`azure-pipelines.yml` deploys the items committed in the `sales-analytics` folder (the Git folder of the sales-analytics workspace) to the **test-sales-analytics** and **prod-sales-analytics** workspaces with [fabric-cicd](https://github.com/microsoft/fabric-cicd).

- **Trigger:** push a tag that points to a commit on `main`, for example:
  ```bash
  git tag v1.0.0 && git push origin v1.0.0
  ```
  Tags on other branches fail the "Verify tag is on main" step.
- **Stages:** `Validate` (tag is on `main`), `Test` (deploys to test-sales-analytics), `Prod` (deploys the same tagged commit to prod-sales-analytics). Test and Prod are deployment jobs that target the Azure DevOps environments `test-sales-analytics` and `prod-sales-analytics`, so **Pipelines > Environments** shows what was deployed to each workspace and when.
- **Approval:** add an **Approvals** check on the `prod-sales-analytics` environment (Pipelines > Environments > prod-sales-analytics > Approvals and checks). The Prod stage then waits for approval after Test succeeds.
- **Bulk publish:** Lakehouse, VariableLibrary, Notebook and SemanticModel are published with the bulk import API (experimental `enable_bulk_publish` flag).
- **Standard publish for PaginatedReport:** paginated reports do not yet support service principals for Git integration and the bulk import API (`PrincipalTypeNotSupported`), so `deploy.py` publishes them in a second, standard pass. This is a temporary workaround only; once paginated reports support service principals for these APIs, the second pass can be removed. `$items.SemanticModel.sm_demo.$id` still resolves because the model was deployed in the first pass.
- **Dynamic parameterization:** `parameter.yml` has no hard-coded IDs. Each `find_value` is a dynamic variable that resolves the value in the source workspace (`$workspace.sales-analytics...`), and each `replace_value` resolves the value in the target workspace.

| Item | What is re-pointed | find_value (source) | replace_value (target) |
|------|--------------------|---------------------|------------------------|
| `nb_demo` | Default lakehouse | `$workspace.sales-analytics.$items.Lakehouse.lh_demo.$id` | `$items.Lakehouse.lh_demo.$id` |
| `nb_demo` | Default lakehouse workspace | `$workspace.sales-analytics.$id` | `$workspace.$id` |
| `sm_demo` | Direct Lake SQL endpoint | `$workspace.sales-analytics.$items.Lakehouse.lh_demo.$sqlendpoint` | `$items.Lakehouse.lh_demo.$sqlendpoint` |
| `sm_demo` | Direct Lake SQL endpoint id | `$workspace.sales-analytics.$items.Lakehouse.lh_demo.$sqlendpointid` | `$items.Lakehouse.lh_demo.$sqlendpointid` |
| `rpt_demo` | Data source semantic model | `$workspace.sales-analytics.$items.SemanticModel.sm_demo.$id` | `$items.SemanticModel.sm_demo.$id` |
| `vl_demo` | `workspace_name` variable | `$.variables[?(@.name=="workspace_name")].value` | `$workspace.$name` |

Pipeline variables: `TENANT_ID`, `CLIENT_ID`, and secret `CLIENT_SECRET`. The service principal needs access to sales-analytics (to resolve source values), test-sales-analytics, and prod-sales-analytics. `deploy-steps.yml` holds the steps shared by both deployment stages.

After deployment, run `nb_demo` in each target workspace to load `dbo.sales`, then refresh `sm_demo` so `rpt_demo` shows data.
