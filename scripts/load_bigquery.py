#!/usr/bin/env python3
"""Load JSONL data files into BigQuery.

Usage:
    # Ensure ADC is set up:
    gcloud auth application-default login

    # Then load data:
    python scripts/load_bigquery.py
"""

import json
import os
import sys

from google.cloud import bigquery

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "reliable-alpha-490519-i1")
DATASET_ID = os.environ.get("BIGQUERY_DATASET", "sap_qm")

# Nested fields that should be stored as JSON-serialized strings
NESTED_FIELDS = {
    "quality_notifications": ["_Item", "_Task", "_Activity"],
    "quality_info_records": ["to_QltyFirstArticleInsp"],
    "controlled_documents": [],
}

TABLE_CONFIG = {
    "quality_notifications": "quality_notifications.jsonl",
    "quality_info_records": "quality_info_records.jsonl",
    "controlled_documents": "controlled_documents.jsonl",
}


def create_dataset(client: bigquery.Client):
    """Create the dataset if it doesn't exist."""
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "US"
    dataset = client.create_dataset(dataset, exists_ok=True)
    print(f"  Dataset ready: {dataset_ref}")


def load_table(client: bigquery.Client, table_name: str, jsonl_file: str):
    """Load a JSONL file into a BigQuery table.

    Nested fields are serialized to JSON strings so the client can
    parse them back into Python objects, matching the previous BigTable
    behaviour.
    """
    filepath = os.path.join(DATA_DIR, jsonl_file)
    nested = NESTED_FIELDS.get(table_name, [])

    with open(filepath) as f:
        records = [json.loads(line) for line in f if line.strip()]

    # Serialize nested fields to JSON strings
    for record in records:
        for field in nested:
            if field in record:
                record[field] = json.dumps(record[field])
        # Ensure all values are strings (matching previous BigTable storage)
        for key, value in list(record.items()):
            if key not in nested and isinstance(value, (dict, list)):
                record[key] = json.dumps(value)
            elif isinstance(value, bool):
                record[key] = str(value).lower()
            elif not isinstance(value, str):
                record[key] = str(value)

    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

    # Build explicit STRING schema from record keys to prevent auto-detect
    # from inferring numeric types for zero-padded IDs like "000300000001"
    all_keys = []
    seen = set()
    for record in records:
        for key in record:
            if key not in seen:
                seen.add(key)
                all_keys.append(key)
    schema = [bigquery.SchemaField(key, "STRING") for key in all_keys]

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    job = client.load_table_from_json(records, table_ref, job_config=job_config)
    job.result()  # Wait for completion

    table = client.get_table(table_ref)
    print(f"  Loaded {table.num_rows} records into {table_name}")


def main():
    client = bigquery.Client(project=PROJECT_ID)

    print("Creating dataset...")
    create_dataset(client)

    print("\nLoading data...")
    for table_name, jsonl_file in TABLE_CONFIG.items():
        load_table(client, table_name, jsonl_file)

    print("\nDone. BigQuery tables loaded successfully.")


if __name__ == "__main__":
    main()
