from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

REQUIRED_COLUMNS = {"pedestrian_id", "frame", "x", "y"}
SAFE_DATASET_ID = re.compile(r"^[a-f0-9]{32}$")


class DatasetValidationError(ValueError):
    pass


class DatasetService:
    """Stores validated trajectory CSVs with generated IDs and metadata.

    Uploads are streamed to a temporary file, size-limited, hashed, validated,
    and then atomically moved into the dataset directory. Original filenames
    are metadata only and are never used as filesystem paths.
    """

    def __init__(
        self,
        upload_dir: str | Path = "data/processed",
        max_upload_bytes: int = 100 * 1024 * 1024,
        max_rows: int = 5_000_000,
    ):
        if max_upload_bytes <= 0 or max_rows <= 0:
            raise ValueError("upload and row limits must be positive")
        self.upload_dir = Path(upload_dir).resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.max_upload_bytes = max_upload_bytes
        self.max_rows = max_rows

    @staticmethod
    def _validate_csv(path: Path, max_rows: int) -> int:
        row_count = 0
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                if not reader.fieldnames:
                    raise DatasetValidationError("CSV has no header row")
                normalized_headers = [name.strip() if name else "" for name in reader.fieldnames]
                if len(set(normalized_headers)) != len(normalized_headers):
                    raise DatasetValidationError("CSV contains duplicate column names")
                reader.fieldnames = normalized_headers
                headers = set(normalized_headers)
                missing = REQUIRED_COLUMNS - headers
                if missing:
                    raise DatasetValidationError(
                        f"CSV is missing required columns: {', '.join(sorted(missing))}"
                    )

                for line_number, row in enumerate(reader, start=2):
                    row_count += 1
                    if row_count > max_rows:
                        raise DatasetValidationError(
                            f"CSV exceeds the maximum of {max_rows} data rows"
                        )
                    try:
                        frame = float(row["frame"])
                        x = float(row["x"])
                        y = float(row["y"])
                        pedestrian_id = str(row["pedestrian_id"]).strip()
                    except (TypeError, ValueError, KeyError) as exc:
                        raise DatasetValidationError(
                            f"Invalid trajectory value on CSV line {line_number}"
                        ) from exc
                    if not pedestrian_id:
                        raise DatasetValidationError(
                            f"Empty pedestrian_id on CSV line {line_number}"
                        )
                    if not all(math.isfinite(v) for v in (frame, x, y)):
                        raise DatasetValidationError(
                            f"Non-finite coordinate/frame on CSV line {line_number}"
                        )
                if row_count == 0:
                    raise DatasetValidationError("CSV contains no trajectory rows")
        except UnicodeDecodeError as exc:
            raise DatasetValidationError("CSV must be UTF-8 encoded") from exc
        except csv.Error as exc:
            raise DatasetValidationError(f"Malformed CSV: {exc}") from exc
        return row_count

    async def save_upload(self, upload) -> dict:
        original_name = (upload.filename or "dataset.csv").replace("\\", "/").rsplit("/", 1)[-1]
        if Path(original_name).suffix.lower() != ".csv":
            raise DatasetValidationError("Only .csv trajectory datasets are supported")

        dataset_id = uuid.uuid4().hex
        final_path = self.upload_dir / f"{dataset_id}.csv"
        temp_path = self.upload_dir / f".{dataset_id}.upload"
        digest = hashlib.sha256()
        size = 0

        try:
            with temp_path.open("xb") as destination:
                while True:
                    chunk = await upload.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > self.max_upload_bytes:
                        raise DatasetValidationError(
                            f"Upload exceeds {self.max_upload_bytes} bytes"
                        )
                    digest.update(chunk)
                    destination.write(chunk)
                destination.flush()
                os.fsync(destination.fileno())

            if size == 0:
                raise DatasetValidationError("Uploaded file is empty")

            row_count = self._validate_csv(temp_path, self.max_rows)
            os.replace(temp_path, final_path)

            metadata = {
                "dataset_id": dataset_id,
                "filename": original_name,
                "stored_filename": final_path.name,
                "size_bytes": size,
                "row_count": row_count,
                "sha256": digest.hexdigest(),
                "format": "csv",
                "status": "validated",
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            }
            metadata_path = self.upload_dir / f"{dataset_id}.json"
            temp_metadata = self.upload_dir / f".{dataset_id}.json.tmp"
            temp_metadata.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            os.replace(temp_metadata, metadata_path)
            return metadata
        except Exception:
            temp_path.unlink(missing_ok=True)
            final_path.unlink(missing_ok=True)
            raise
        finally:
            await upload.close()

    def list_datasets(self) -> list[dict]:
        results = []
        for metadata_path in sorted(self.upload_dir.glob("*.json")):
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                dataset_id = metadata.get("dataset_id", "")
                data_path = self.upload_dir / f"{dataset_id}.csv"
                if SAFE_DATASET_ID.fullmatch(dataset_id) and data_path.is_file():
                    results.append(metadata)
            except (OSError, json.JSONDecodeError):
                continue
        return results

    def get_dataset_path(self, dataset_id: str) -> Path:
        if not SAFE_DATASET_ID.fullmatch(dataset_id):
            raise FileNotFoundError("Dataset not found")
        path = self.upload_dir / f"{dataset_id}.csv"
        metadata = self.upload_dir / f"{dataset_id}.json"
        if not path.is_file() or not metadata.is_file():
            raise FileNotFoundError("Dataset not found")
        return path
