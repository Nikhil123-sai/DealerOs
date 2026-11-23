
from collections import defaultdict
from decimal import Decimal

from .models import Location, SystemARecord, SystemBEntry


def get_disagreements(org_id):
    """
    Compare System A and System B for one organization.

    Returns a list of disagreement dictionaries.
    """
    if not Location.objects.filter(org_id=org_id).exists():
        return []

    locations = set(
        Location.objects.filter(org_id=org_id)
        .values_list("location_id", flat=True)
    )

    records_a = list(
        SystemARecord.objects.filter(
            location_id__in=locations
        )
    )

    # Only load System B entries belonging to this tenant.
    entries_b = list(
        SystemBEntry.objects.filter(
            location_id__in=locations
        )
    )

    a_by_id = {record.record_id: record for record in records_a}
    b_by_ref = defaultdict(list)

    for entry in entries_b:
        b_by_ref[entry.normalized_record_ref].append(entry)

    disagreements = []

    for record in records_a:
        entries = b_by_ref.get(record.record_id, [])

        if not entries:
            disagreements.append({
                "record_id": record.record_id,
                "location_id": record.location_id,
                "reason": "MISSING_IN_B",
                "system_a_value": record.total_value,
                "system_b_value": None,
            })
            continue

        # Missing amounts are unknown, not zero.
        if any(entry.value is None for entry in entries):
            disagreements.append({
                "record_id": record.record_id,
                "location_id": record.location_id,
                "reason": "VALUE_MISMATCH",
                "system_a_value": record.total_value,
                "system_b_value": None,
            })
            continue

        b_total = sum(
            (entry.value for entry in entries),
            Decimal("0.00"),
        )

        if len(entries) > 1 and all(
            entry.value == record.total_value for entry in entries
        ):
            reason = "DUPLICATE_IN_B"
        elif b_total != record.total_value:
            reason = "VALUE_MISMATCH"
        else:
            continue

        disagreements.append({
            "record_id": record.record_id,
            "location_id": record.location_id,
            "reason": reason,
            "system_a_value": record.total_value,
            "system_b_value": b_total,
        })


    for reference, entries in b_by_ref.items():
        if reference not in a_by_id:
            # Check whether the reference belongs to another tenant.
            # Do not expose the other tenant's location or amount.
            belongs_to_other_org = SystemARecord.objects.filter(
                record_id=reference
            ).exclude(
                location__org_id=org_id
            ).exists()

            for entry in entries:
                disagreements.append({
                    "record_id": reference,
                    "location_id": entry.location_id,
                    "reason": (
                        "LOCATION_MISMATCH"
                        if belongs_to_other_org
                        else "ORPHAN_IN_B"
                    ),
                    "system_a_value": None,
                    "system_b_value": entry.value,
                })


    return disagreements
