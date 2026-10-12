# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "11111111-1111-1111-1111-111111111111",
# META       "default_lakehouse_name": "lh_demo",
# META       "default_lakehouse_workspace_id": "22222222-2222-2222-2222-222222222222",
# META       "known_lakehouses": [
# META         {
# META           "id": "11111111-1111-1111-1111-111111111111"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # nb_demo
# Writes a small `sales` table to the default lakehouse (`lh_demo`). The `sm_demo` Direct Lake semantic model and the `rpt_demo` paginated report read this table.

# CELL ********************

from pyspark.sql import Row

rows = [
    Row(region="North", product="Bikes", amount=1200.0),
    Row(region="North", product="Helmets", amount=150.0),
    Row(region="South", product="Bikes", amount=980.0),
    Row(region="South", product="Gloves", amount=75.5),
    Row(region="East", product="Bikes", amount=1430.0),
    Row(region="East", product="Helmets", amount=210.0),
    Row(region="West", product="Gloves", amount=99.9),
    Row(region="West", product="Bikes", amount=1105.0),
]

df = spark.createDataFrame(rows)
df.write.mode("overwrite").option("overwriteSchema", "true").format("delta").saveAsTable("dbo.sales")
display(spark.table("dbo.sales"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
