# Demo items (fabric-cicd)

Item definitions (Fabric Git format) in `workspace/`, deployed to a workspace with [fabric-cicd](https://github.com/microsoft/fabric-cicd) by `azure-pipelines.yml`.

| Item | Type | Notes |
|------|------|-------|
| `lh_demo` | Lakehouse | Schema-enabled (`dbo`) |
| `nb_demo` | Notebook | Default lakehouse is `lh_demo`; writes the `dbo.sales` table |
| `vl_demo` | Variable library | `workspace_name` = `sales-analytics` |
| `sm_demo` | Semantic model | Direct Lake on the `lh_demo` SQL analytics endpoint, table `sales` |
| `rpt_demo` | Paginated report | Sales by region, data source is `sm_demo` |

Item references use placeholder IDs that `workspace/parameter.yml` replaces with the deployed IDs (`$items.*`, `$workspace.$id`).

`deploy.py` runs in this order:

1. Publish the variable library, lakehouse, and notebook.
2. Run `nb_demo` to create `dbo.sales`, then sync the lakehouse SQL analytics endpoint.
3. Publish the semantic model and paginated report.
4. Refresh `sm_demo` so the report has data.

The service principal needs Admin or Member on the target workspace. Set the secret pipeline variable `CLIENT_SECRET` before running.
