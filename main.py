import subprocess
import sys
from pathlib import Path

# Sets the base directory to the folder where this script is located
BASE_DIR = Path(__file__).resolve().parent

# Defines the sequence of pipeline steps with descriptive names and corresponding script paths
PIPELINE_STEPS = [
    #("Extract UN Comtrade data", "src/extract_comtrade.py"),
    #("Extract World Bank data", "src/extract_worldbank.py"),
    #("Extract and clean CBP data", "src/extract_cbp.py"),
    #("Upload raw data to Azure Blob", "src/upload_to_blob.py"),
    #("Clean data using Spark", "src/spark_cleaning.py"),
    #("Run Analysis 1: Qatar demand surge", "src/spark_analysis1_qatar.py"),
    #("Run Analysis 2: Host country comparison", "src/spark_analysis2_comparison.py"),
    #("Run Analysis 3: Stocking prediction", "src/spark_analysis3_prediction.py"),
    #("Write analysis outputs to PostgreSQL", "src/write_to_postgres.py"),
    ("Extract from PostgresSQL for Follow-up Analysis", "src/extract_for_analysis.py"),
    ("Perform Follow-up Analysis", "src/followup_analysis.py")
]

def run_step(step_name, script_path):
    # Prints a separator and the name of the pipeline step being executed
    print("\n" + "=" * 80)
    print(f"STARTING: {step_name}")
    print("=" * 80)

    # Constructs the full file path to the script
    full_path = BASE_DIR / script_path

    # Checks if the script exists before attempting to run it
    if not full_path.exists():
        raise FileNotFoundError(f"Script not found: {full_path}")

    # Executes the script using the current Python interpreter
    result = subprocess.run(
        [sys.executable, str(full_path)],
        cwd=BASE_DIR
    )

    # Checks if the script execution failed (non-zero return code)
    if result.returncode != 0:
        raise RuntimeError(f"Pipeline failed at step: {step_name}")

    # Prints confirmation that the step completed successfully
    print(f"COMPLETED: {step_name}")

def main():
    # Prints a message indicating the pipeline execution has started
    print("\nWorld Cup Demand Surge Pipeline Started")

    # Iterates through each pipeline step and executes it sequentially
    for step_name, script_path in PIPELINE_STEPS:
        run_step(step_name, script_path)

    # Prints a final success message after all steps are completed
    print("\nPipeline completed successfully.")
    print("Outputs are available in Azure Blob Storage and PostgreSQL/Supabase.")

# Ensures the pipeline runs only when this script is executed directly
if __name__ == "__main__":
    main()