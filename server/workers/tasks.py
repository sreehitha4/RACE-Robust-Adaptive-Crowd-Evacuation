"""Background tasks are deliberately limited to offline jobs, never live frame stepping."""
from pathlib import Path
from server.workers.celery_app import celery_app

@celery_app.task(name="race.validate_dataset")
def validate_dataset(dataset_path: str):
    path = Path(dataset_path).resolve()
    if not path.is_file() or path.suffix.lower() != ".csv":
        raise ValueError("A readable CSV dataset path is required")
    import csv
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"pedestrian_id", "frame", "x", "y"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError("Dataset schema is not normalized RACE trajectory CSV")
        count = sum(1 for _ in reader)
    return {"path": str(path), "rows": count, "status": "validated"}
