from __future__ import annotations

import hashlib
import json
import random
import uuid
from datetime import timezone

from faker import Faker

from schematico.schema import FieldSpec

fake = Faker()


def _generate_value(field: FieldSpec) -> object:
    match field.type:
        case "uuid":
            return str(uuid.uuid4())
        case "full_name":
            return fake.name()
        case "email":
            return fake.email()
        case "enum":
            return random.choice(field.values)
        case "country":
            return fake.country()
        case "timestamp":
            return fake.date_time(tzinfo=timezone.utc).isoformat()
        case "int" | "integer":
            lo = int(field.min) if field.min is not None else 0
            hi = int(field.max) if field.max is not None else 100_000
            return random.randint(lo, hi)
        case "string":
            return fake.word()
        case "boolean":
            return random.choice([True, False])
        case "float" | "decimal":
            lo = float(field.min) if field.min is not None else 0.0
            hi = float(field.max) if field.max is not None else 1.0
            return round(random.uniform(lo, hi), 4)
        case _:
            raise ValueError(f"Unsupported type: {field.type}")


def _hash_record(record: dict) -> str:
    serialized = json.dumps(record, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()
