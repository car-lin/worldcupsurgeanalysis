from urllib.parse import urlparse, unquote

# Imports SparkSession to create a Spark environment
from pyspark.sql import SparkSession

# Imports helper functions to load configuration and environment variables
from settings import load_config, get_env

# Loads configuration values from the YAML config file
cfg = load_config()

# Retrieves Azure Blob Storage connection string from environment variables
connection_string = get_env("AZURE_STORAGE_CONNECTION_STRING")

# Gets the Azure container name from the configuration
container = cfg["azure"]["container_name"]

# Retrieves PostgreSQL (Supabase) connection URL from environment variables
postgres_url = get_env("POSTGRES_URL")

# Azure connection details
# Parses the Azure connection string into key-value pairs
parts = dict(item.split("=", 1) for item in connection_string.split(";") if "=" in item)

# Extracts storage account name and account key
account_name = parts["AccountName"]
account_key = parts["AccountKey"]

# Parse Supabase/PostgreSQL URL
# Parses the PostgreSQL URL into components
parsed = urlparse(postgres_url)

# Decodes username and password (handles URL-encoded characters)
db_user = unquote(parsed.username)
db_password = unquote(parsed.password)

# Extracts host, port, and database name
db_host = parsed.hostname
db_port = parsed.port
db_name = parsed.path.replace("/", "")

# Constructs the JDBC connection URL with SSL enabled
jdbc_url = f"jdbc:postgresql://{db_host}:{db_port}/{db_name}?sslmode=require"

# Initializes a Spark session with required dependencies for Azure and PostgreSQL
spark = (
    SparkSession.builder
    .appName("WriteResultsToPostgres")
    .config("spark.driver.host", "127.0.0.1")
    .config("spark.driver.bindAddress", "127.0.0.1")
    .config(
        "spark.jars.packages",
        "org.apache.hadoop:hadoop-azure:3.3.4,"
        "com.microsoft.azure:azure-storage:8.6.6,"
        "org.postgresql:postgresql:42.7.3"
    )
    .getOrCreate()
)

# Azure Blob access
# Configures Spark to authenticate with Azure Blob Storage
spark._jsc.hadoopConfiguration().set(
    f"fs.azure.account.key.{account_name}.blob.core.windows.net",
    account_key
)

# Constructs the base Azure Blob Storage path
base_path = f"wasbs://{container}@{account_name}.blob.core.windows.net"

# Defines PostgreSQL connection properties for Spark JDBC write
db_properties = {
    "user": db_user,
    "password": db_password,
    "driver": "org.postgresql.Driver"
}

# Maps PostgreSQL table names to corresponding Azure Blob Storage paths
tables = {
    "commodity_surges_qatar": "processed/analysis1/top_commodities",
    "qatar_monthly_import_trend": "processed/analysis1/monthly_trend",
    "worldbank_indicator_trends": "processed/analysis2/worldbank_indicator_trends",
    "import_by_country_year": "processed/analysis2/import_by_country_year",
    "host_country_comparison": "processed/analysis2/host_country_comparison",
    "predicted_stocking_opportunities": "processed/analysis3/prediction",
}

# Loops through each table and writes data from Blob Storage to PostgreSQL
for table_name, blob_path in tables.items():
    # Prints the table currently being processed
    print(f"Writing {table_name}...")

    # Reads the CSV data from Azure Blob Storage
    df = spark.read.csv(
        f"{base_path}/{blob_path}",
        header=True,
        inferSchema=True
    )

    # Writes the dataframe to PostgreSQL using JDBC connection
    df.write.jdbc(
        url=jdbc_url,
        table=table_name,
        mode="overwrite",
        properties=db_properties
    )

    # Prints confirmation after saving each table
    print(f"Saved: {table_name}")

# Stops the Spark session to release resources
spark.stop()

# Prints final confirmation after all tables are written
print("\nAll analysis outputs written to Supabase/PostgreSQL.")