from pathlib import Path
from azure.storage.blob import BlobServiceClient

# Imports helper functions to load configuration and environment variables
from settings import load_config, get_env

# Sets the base project directory by moving one level up from the current script location
BASE_DIR = Path(__file__).resolve().parents[1]

# Loads configuration values from the YAML config file
cfg = load_config()

# Retrieves Azure Blob Storage connection string from environment variables
connection_string = get_env("AZURE_STORAGE_CONNECTION_STRING")

# Gets the Azure Blob Storage container name from the configuration
container_name = cfg["azure"]["container_name"]

# Creates a BlobServiceClient using the Azure connection string
blob_service = BlobServiceClient.from_connection_string(connection_string)

# Gets the specific Azure Blob container client where files will be uploaded
container_client = blob_service.get_container_client(container_name)

# Defines local files and their target paths inside Azure Blob Storage
files_to_upload = [
    {
        "local_path": BASE_DIR / "data" / "temp" / "worldbank_indicators.csv",
        "blob_path": "raw/worldbank/worldbank_indicators.csv"
    },
    {
        "local_path": BASE_DIR / "data" / "temp" / "comtrade" / "comtrade_QAT.csv",
        "blob_path": "raw/comtrade/comtrade_QAT.csv"
    },
    {
        "local_path": BASE_DIR / "data" / "temp" / "comtrade" / "comtrade_USA.csv",
        "blob_path": "raw/comtrade/comtrade_USA.csv"
    },
    {
        "local_path": BASE_DIR / "data" / "temp" / "comtrade" / "comtrade_CAN.csv",
        "blob_path": "raw/comtrade/comtrade_CAN.csv"
    },
    {
        "local_path": BASE_DIR / "data" / "temp" / "comtrade" / "comtrade_MEX.csv",
        "blob_path": "raw/comtrade/comtrade_MEX.csv"
    },
    {
        "local_path": BASE_DIR / "data" / "temp" / "cbp_filtered.csv",
        "blob_path": "raw/cbp/cbp_filtered.csv"
    },
    {
        "local_path": BASE_DIR / "config" / "event_metadata.csv",
        "blob_path": "raw/events/event_metadata.csv"
    }
]

# Loops through each file listed for upload
for item in files_to_upload:
    # Gets the local file path
    local_path = item["local_path"]

    # Gets the destination path inside Azure Blob Storage
    blob_path = item["blob_path"]

    # Skips the upload if the local file does not exist
    if not local_path.exists():
        print(f"Skipped, file not found: {local_path}")
        continue

    # Opens the local file in binary read mode for upload
    with open(local_path, "rb") as file:
        # Uploads the file to Azure Blob Storage and overwrites any existing file with the same name
        container_client.upload_blob(
            name=blob_path,
            data=file,
            overwrite=True
        )

    # Prints confirmation after each successful upload
    print(f"Uploaded: {local_path} -> {blob_path}")

# Prints final confirmation after all available files have been processed
print("\nAll available files uploaded to Azure Blob Storage.")