# pharmalizer_v2/app/licensing/validator.py
import json
import uuid
from dataclasses import dataclass
from typing import List, Dict


LICENSE_KEYS: List[Dict[str, str]] = [
    {"license_key": "ABC123XYZ", "expiration_date": "2025-12-31"},
    {"license_key": "DEF456LMN", "expiration_date": "2028-12-31"},
]


def get_device_id() -> str:
    return str(uuid.getnode())


def validate_license_file(file_path: str) -> bool:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            license_data = json.load(f)

        license_key = license_data.get("license_key")
        expiration_date = license_data.get("expiration_date")
        device_id = license_data.get("device_id")

        # device_id yoksa bu cihazı yaz
        if not device_id:
            license_data["device_id"] = get_device_id()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(license_data, f, indent=4)
        elif device_id != get_device_id():
            return False

        # key + expiration kontrolü
        for item in LICENSE_KEYS:
            if item["license_key"] == license_key:
                return expiration_date <= item["expiration_date"]

    except Exception:
        return False

    return False
