#!/usr/bin/env python3
"""Load JSONL data files into BigTable emulator.

Usage:
    # Start the emulator first:
    docker compose up -d

    # Then load data:
    BIGTABLE_EMULATOR_HOST=localhost:8086 python scripts/load_bigtable.py
"""

import json
import os
import sys

from google.cloud import bigtable
from google.cloud.bigtable import column_family as cf

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

COLUMN_FAMILY = "data"
PROJECT_ID = os.environ.get("BIGTABLE_PROJECT_ID", "box-sap-sapphire")
INSTANCE_ID = os.environ.get("BIGTABLE_INSTANCE_ID", "sap-demo")

# Nested fields that should be stored as JSON-serialized values
NESTED_FIELDS = {
    "quality_notifications": ["_Item", "_Task", "_Activity"],
    "quality_info_records": ["to_QltyFirstArticleInsp"],
    "controlled_documents": [],
}


def row_key_quality_notification(r: dict) -> str:
    return f"{r['NotificationType']}#{r['NotificationStatus']}#{r['QualityNotification']}"


def row_key_quality_info_record(r: dict) -> str:
    return f"{r['Plant']}#{r['Material']}#{r['QltyInProcmtIntID']}"


def row_key_controlled_document(r: dict) -> str:
    return f"{r['DocumentType']}#{r['Status']}#{r['DocumentID']}"


def secondary_keys_notification(r: dict) -> list[str]:
    """Generate secondary index keys for material-based lookups."""
    keys = []
    if r.get("Material"):
        keys.append(f"MAT#{r['Material']}#{r['QualityNotification']}")
    if r.get("Supplier"):
        keys.append(f"SUP#{r['Supplier']}#{r['QualityNotification']}")
    return keys


def secondary_keys_quality_info(r: dict) -> list[str]:
    """Generate secondary index keys for supplier-based lookups."""
    keys = []
    if r.get("Supplier"):
        keys.append(f"SUP#{r['Supplier']}#{r['Material']}#{r['QltyInProcmtIntID']}")
    return keys


def secondary_keys_controlled_doc(r: dict) -> list[str]:
    """Generate secondary index keys for CAPA and ISO reference lookups."""
    keys = []
    capa_refs = r.get("RelatedCAPAReference", "")
    if capa_refs:
        for ref in capa_refs.split(", "):
            ref = ref.strip()
            if ref:
                keys.append(f"CAPA#{ref}#{r['DocumentID']}")
    iso_ref = r.get("ISOReference", "")
    if iso_ref:
        keys.append(f"ISO#{iso_ref}#{r['DocumentID']}")
    return keys


TABLE_CONFIG = {
    "quality_notifications": {
        "file": "quality_notifications.jsonl",
        "row_key_fn": row_key_quality_notification,
        "secondary_keys_fn": secondary_keys_notification,
    },
    "quality_info_records": {
        "file": "quality_info_records.jsonl",
        "row_key_fn": row_key_quality_info_record,
        "secondary_keys_fn": secondary_keys_quality_info,
    },
    "controlled_documents": {
        "file": "controlled_documents.jsonl",
        "row_key_fn": row_key_controlled_document,
        "secondary_keys_fn": secondary_keys_controlled_doc,
    },
}


def _set_row_cells(row, record: dict, nested_fields: list[str]):
    """Set all cells on a BigTable row from a record dict."""
    for key, value in record.items():
        if key in nested_fields:
            row.set_cell(COLUMN_FAMILY, key.encode(), json.dumps(value).encode())
        elif isinstance(value, (dict, list)):
            row.set_cell(COLUMN_FAMILY, key.encode(), json.dumps(value).encode())
        elif isinstance(value, bool):
            row.set_cell(COLUMN_FAMILY, key.encode(), str(value).lower().encode())
        else:
            row.set_cell(COLUMN_FAMILY, key.encode(), str(value).encode())


def create_tables(instance):
    """Create BigTable tables with column families."""
    for table_name in TABLE_CONFIG:
        table = instance.table(table_name)
        if not table.exists():
            table.create(column_families={COLUMN_FAMILY: cf.MaxVersionsGCRule(1)})
            print(f"  Created table: {table_name}")
        else:
            print(f"  Table exists: {table_name}")


def load_table(instance, table_name: str, config: dict):
    """Load a JSONL file into a BigTable table with primary and secondary keys."""
    table = instance.table(table_name)
    filepath = os.path.join(DATA_DIR, config["file"])
    nested = NESTED_FIELDS.get(table_name, [])

    with open(filepath) as f:
        records = [json.loads(line) for line in f if line.strip()]

    rows = []
    for record in records:
        # Primary row
        row_key = config["row_key_fn"](record)
        row = table.direct_row(row_key)
        _set_row_cells(row, record, nested)
        rows.append(row)

        # Secondary index rows (duplicate data for cross-queries)
        for sec_key in config["secondary_keys_fn"](record):
            sec_row = table.direct_row(sec_key)
            _set_row_cells(sec_row, record, nested)
            rows.append(sec_row)

    table.mutate_rows(rows)
    sec_count = len(rows) - len(records)
    print(f"  Loaded {len(records)} records + {sec_count} index rows into {table_name}")


def main():
    os.environ.setdefault("BIGTABLE_EMULATOR_HOST", "localhost:8086")

    client = bigtable.Client(project=PROJECT_ID, admin=True)
    instance = client.instance(INSTANCE_ID)

    print("Creating tables...")
    create_tables(instance)

    print("\nLoading data...")
    for table_name, config in TABLE_CONFIG.items():
        load_table(instance, table_name, config)

    print("\nDone. BigTable emulator loaded successfully.")


if __name__ == "__main__":
    main()
