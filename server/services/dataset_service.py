
"""Bounded, validated CSV ingestion for normalized pedestrian trajectories."""

import csv
import hashlib
import json
import math
import os
import re
import uuid
from pathlib import Path

from fastapi import UploadFile


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET_DIR = ROOT / "data" / "datasets"

REQUIRED_COLUMNS = {"pedestrian_id", "frame", "x", "y"}
DATASET_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")


class DatasetValidationError(ValueError):
    """Raised when an uploaded dataset fails validation."""


class DatasetService:
    def __init__(
        self,
        directory=DEFAULT_DATASET_DIR,
        max_bytes=100 * 1024 * 1024,
        max_rows=5_000_000,
    ):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes
        self.max_rows = max_rows

    def get_dataset_path(self, dataset_id):
        if not isinstance(dataset_id, str) or not DATASET_ID_PATTERN.fullmatch(dataset_id):
            raise DatasetValidationError("Invalid dataset identifier")

        return self.directory / f"{dataset_id}.csv"

    async def save(self, upload: UploadFile):
        original_name = str(upload.filename or "")

        # Normalize both Windows and POSIX path separators.
        safe_name = original_name.replace("\\", "/").split("/")[-1]

        if not safe_name or Path(safe_name).suffix.lower() != ".csv":
            raise DatasetValidationError("Only .csv files are accepted")

        dataset_id = uuid.uuid4().hex
        temp = self.directory / f".{dataset_id}.upload"
        target = self.directory / f"{dataset_id}.csv"

        digest = hashlib.sha256()
        size = 0

        try:
            with temp.open("wb") as output:
                while True:
                    chunk = await upload.read(1024 * 1024)

                    if not chunk:
                        break

                    size += len(chunk)

                    if size > self.max_bytes:
                        raise DatasetValidationError(
                            "Upload exceeds configured size limit"
                        )

                    digest.update(chunk)
                    output.write(chunk)

            if size == 0:
                raise DatasetValidationError("Uploaded CSV is empty")

            row_count = 0

            with temp.open("r", encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                columns = set(reader.fieldnames or [])

                if not REQUIRED_COLUMNS.issubset(columns):
                    missing = sorted(REQUIRED_COLUMNS - columns)
                    raise DatasetValidationError(
                        f"CSV must contain columns: {', '.join(missing)}"
                    )

                for row in reader:
                    row_count += 1

                    if row_count > self.max_rows:
                        raise DatasetValidationError(
                            "CSV exceeds configured row limit"
                        )

                    try:
                        frame = float(row["frame"])
                        x = float(row["x"])
                        y = float(row["y"])
                    except (TypeError, ValueError, KeyError):
                        raise DatasetValidationError(
                            f"Invalid numeric value at data row {row_count}"
                        )

                    if not all(math.isfinite(value) for value in (frame, x, y)):
                        raise DatasetValidationError(
                            f"Non-finite coordinate at data row {row_count}"
                        )

                    if not row["pedestrian_id"]:
                        raise DatasetValidationError(
                            f"Missing pedestrian_id at data row {row_count}"
                        )

            if row_count == 0:
                raise DatasetValidationError(
                    "CSV contains no trajectory rows"
                )

            # Atomically move the validated CSV into its final location.
            os.replace(temp, target)

            metadata = {
                "dataset_id": dataset_id,
                "filename": safe_name,
                "stored_filename": target.name,
                "bytes": size,
                "rows": row_count,
                "row_count": row_count,
                "sha256": digest.hexdigest(),
                "schema": sorted(REQUIRED_COLUMNS),
                "status": "validated",
            }

            metadata_path = self.directory / f"{dataset_id}.json"
            metadata_temp = self.directory / f".{dataset_id}.json.tmp"

            try:
                metadata_temp.write_text(
                    json.dumps(metadata, indent=2),
                    encoding="utf-8",
                )
                os.replace(metadata_temp, metadata_path)
            finally:
                metadata_temp.unlink(missing_ok=True)

            return metadata

        finally:
            temp.unlink(missing_ok=True)

    async def save_upload(self, upload):
        """Compatibility method for the dataset lifecycle interface."""
        return await self.save(upload)

    def list(self):
        datasets = []

        for path in sorted(self.directory.glob("*.json")):
            try:
                datasets.append(
                    json.loads(path.read_text(encoding="utf-8"))
                )
            except (OSError, json.JSONDecodeError):
                continue

        return datasets
