
import csv
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from reconcile.models import Location, SystemARecord, SystemBEntry


def normalize_reference(value):
    """Convert messy System B references to REC-1234 format."""
    cleaned = re.sub(r"\s+", "", value).upper()
    match = re.fullmatch(r"(?:REC-?)?(\d+)", cleaned)

    if match:
        return f"REC-{match.group(1)}"

    return cleaned


def parse_amount(value, allow_blank=False):
    """Parse monetary values without using floating-point numbers."""
    cleaned = value.strip().replace(",", "")

    if not cleaned:
        if allow_blank:
            return None
        raise ValueError("Required monetary amount is blank")

    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid monetary amount: {value!r}") from exc


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        yield from csv.DictReader(file)


class Command(BaseCommand):
    help = "Import DealerOS locations, System A and System B CSV data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-dir",
            type=Path,
            default=Path(__file__).resolve().parents[4]
            / "DealerOS_Assignment_Dataset",
            help="Directory containing the three CSV files.",
        )

    def handle(self, *args, **options):
        data_dir = options["data_dir"]

        for filename in ("locations.csv", "system_a.csv", "system_b.csv"):
            if not (data_dir / filename).is_file():
                raise CommandError(f"Missing CSV file: {data_dir / filename}")

        try:
            with transaction.atomic():
                for row in read_csv(data_dir / "locations.csv"):
                    Location.objects.update_or_create(
                        location_id=row["location_id"],
                        defaults={
                            "org_id": row["org_id"],
                            "location_name": row["location_name"],
                        },
                    )

                for row in read_csv(data_dir / "system_a.csv"):
                    SystemARecord.objects.update_or_create(
                        record_id=row["record_id"],
                        defaults={
                            "location_id": row["location_id"],
                            "event_date": date.fromisoformat(row["event_date"]),
                            "category_code": row["category_code"],
                            "actor_id": row["actor_id"],
                            "base_value": parse_amount(row["base_value"]),
                            "adjustment": parse_amount(row["adjustment"]),
                            "total_value": parse_amount(row["total_value"]),
                            "state": row["state"],
                        },
                    )

                for row in read_csv(data_dir / "system_b.csv"):
                    SystemBEntry.objects.update_or_create(
                        entry_id=row["entry_id"],
                        defaults={
                            "record_ref": row["record_ref"],
                            "normalized_record_ref": normalize_reference(
                                row["record_ref"]
                            ),
                            "location_id": row["location_id"],
                            "recorded_on": (
                                date.fromisoformat(row["recorded_on"])
                                if row["recorded_on"].strip()
                                else None
                            ),
                            "value": parse_amount(
                                row["value"], allow_blank=True
                            ),
                            "raw_value": row["value"],
                            "label": row["label"],
                        },
                    )

        except (ValueError, KeyError, OSError) as exc:
            raise CommandError(f"CSV import failed: {exc}") from exc

        self.stdout.write(
            self.style.SUCCESS(
                "Import complete: "
                f"{Location.objects.count()} locations, "
                f"{SystemARecord.objects.count()} System A records, "
                f"{SystemBEntry.objects.count()} System B entries."
            )
        )
