"""Execute all pipeline notebooks in sequence with the project as the working directory."""
import nbformat
from nbclient import NotebookClient
import os, sys, time

PROJECT = "/Users/amolprakash/Desktop/Mckinesy/Untitled"

NOTEBOOKS = [
    "01_data_loading_exploration.ipynb",
    "02_data_combination_preprocessing.ipynb",
    "03_target_variable_creation.ipynb",
    "04_feature_engineering.ipynb",
    "05_model_development.ipynb",
]

for nb_name in NOTEBOOKS:
    nb_path = os.path.join(PROJECT, nb_name)
    print(f"\n{'='*60}")
    print(f"Running {nb_name} ...")
    print(f"{'='*60}")
    t0 = time.time()

    with open(nb_path) as f:
        nb = nbformat.read(f, as_version=4)

    client = NotebookClient(
        nb,
        timeout=7200,
        kernel_name="python3",
        resources={"metadata": {"path": PROJECT}},
    )

    try:
        client.execute()
        elapsed = time.time() - t0
        print(f"OK  {nb_name}  ({elapsed:.0f}s)")
    except Exception as e:
        print(f"FAILED {nb_name}: {e}", file=sys.stderr)
        sys.exit(1)

    with open(nb_path, "w") as f:
        nbformat.write(nb, f)
    print(f"Saved {nb_path}")

print("\nAll notebooks complete.")
