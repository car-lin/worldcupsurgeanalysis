from pyspark.sql import SparkSession
from settings import load_config, get_env

cfg = load_config()

connection_string = get_env("AZURE_STORAGE_CONNECTION_STRING")
container = cfg["azure"]["container_name"]

parts = dict(item.split("=", 1) for item in connection_string.split(";") if "=" in item)
account_name = parts["AccountName"]
account_key = parts["AccountKey"]

spark = (
    SparkSession.builder
    .appName("CheckData")
    .config(
        "spark.jars.packages",
        "org.apache.hadoop:hadoop-azure:3.3.4,com.microsoft.azure:azure-storage:8.6.6"
    )
    .getOrCreate()
)

spark._jsc.hadoopConfiguration().set(
    f"fs.azure.account.key.{account_name}.blob.core.windows.net",
    account_key
)

base_path = f"wasbs://{container}@{account_name}.blob.core.windows.net"

comtrade = spark.read.csv(f"{base_path}/processed/comtrade_clean", header=True)
worldbank = spark.read.csv(f"{base_path}/processed/worldbank_clean", header=True)
cbp = spark.read.csv(f"{base_path}/processed/cbp_clean", header=True)

print("Comtrade rows:", comtrade.count())
print("Distinct commodity codes:")
comtrade.select("commodity_code").distinct().show(50, truncate=False)

print("Non-TOTAL rows:")
print(comtrade.filter(comtrade.commodity_code != "TOTAL").count())
print("WorldBank rows:", worldbank.count())
print("CBP rows:", cbp.count())

print("\nComtrade sample:")
comtrade.show(5, truncate=False)

print("\nWorld Bank sample:")
worldbank.show(5, truncate=False)

print("\nCBP sample:")
cbp.show(5, truncate=False)

spark.stop()
