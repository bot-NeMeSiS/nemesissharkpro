
"""
NeMeSiS SHARK PRO V69
Dataset export helper
"""

import csv
import json
import sqlite3
from pathlib import Path


def export_ml_dataset_csv(db_path="nemesis.db", output_path="exports/shark_ml_dataset.csv"):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM shark_ml_dataset ORDER BY created_at DESC").fetchall()
    conn.close()

    if not rows:
        Path(output_path).write_text("", encoding="utf-8")
        return output_path

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))

    return output_path


def export_ml_dataset_json(db_path="nemesis.db", output_path="exports/shark_ml_dataset.json"):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM shark_ml_dataset ORDER BY created_at DESC").fetchall()
    conn.close()

    data = [dict(row) for row in rows]
    Path(output_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return output_path
