
from django.test import TestCase

from reconcile.models import Location, SystemARecord, SystemBEntry
from reconcile.services import get_disagreements


class ReconciliationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        Location.objects.create(
            location_id="LOC-101",
            org_id="ORG-A",
            location_name="Test A",
        )

        Location.objects.create(
            location_id="LOC-201",
            org_id="ORG-B",
            location_name="Test B",
        )

        for record_id, total in [
            ("REC-1042", "100.00"),
            ("REC-1055", "100.00"),
            ("REC-1077", "100.00"),
        ]:
            SystemARecord.objects.create(
                record_id=record_id,
                location_id="LOC-101",
                event_date="2026-01-01",
                category_code="TEST",
                actor_id="TEST",
                base_value=total,
                adjustment="0.00",
                total_value=total,
                state="COMPLETE",
            )

        for entry_id, ref, location, value in [
            ("E1", "REC-1042", "LOC-101", "100.00"),
            ("E2", "REC-1042", "LOC-101", "100.00"),
            ("E3", "REC-1055", "LOC-101", "40.00"),
            ("E4", "REC-1055", "LOC-101", "60.00"),
            ("E5", "REC-1077", "LOC-201", "100.00"),
        ]:
            SystemBEntry.objects.create(
                entry_id=entry_id,
                record_ref=ref,
                normalized_record_ref=ref,
                location_id=location,
                recorded_on="2026-01-01",
                value=value,
                raw_value=value,
                label="Test",
            )

    def test_duplicate_detected(self):
        results = get_disagreements("ORG-A")
        reasons = [
            item["reason"]
            for item in results
            if item["record_id"] == "REC-1042"
        ]
        self.assertEqual(reasons, ["DUPLICATE_IN_B"])

    def test_valid_split_not_flagged(self):
        results = get_disagreements("ORG-A")
        self.assertFalse(
            any(item["record_id"] == "REC-1055" for item in results)
        )

    def test_cross_tenant_mismatch_hides_system_a_value(self):
        results = get_disagreements("ORG-B")
        matches = [
            item for item in results
            if item["record_id"] == "REC-1077"
        ]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["reason"], "LOCATION_MISMATCH")
        self.assertIsNone(matches[0]["system_a_value"])
        self.assertEqual(matches[0]["location_id"], "LOC-201")

    def test_null_amount_is_value_mismatch(self):
        SystemARecord.objects.create(
            record_id="REC-NULL",
            location_id="LOC-101",
            event_date="2026-01-01",
            category_code="TEST",
            actor_id="TEST",
            base_value="250.00",
            adjustment="0.00",
            total_value="250.00",
            state="COMPLETE",
        )

        SystemBEntry.objects.create(
            entry_id="E-NULL",
            record_ref="REC-NULL",
            normalized_record_ref="REC-NULL",
            location_id="LOC-101",
            recorded_on="2026-01-01",
            value=None,
            raw_value="",
            label="Missing amount",
        )

        results = get_disagreements("ORG-A")
        matches = [
            item for item in results
            if item["record_id"] == "REC-NULL"
        ]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["reason"], "VALUE_MISMATCH")
        self.assertIsNone(matches[0]["system_b_value"])

    def test_tenant_isolation(self):
        SystemARecord.objects.create(
            record_id="REC-PRIVATE-B",
            location_id="LOC-201",
            event_date="2026-01-01",
            category_code="TEST",
            actor_id="TEST",
            base_value="500.00",
            adjustment="0.00",
            total_value="500.00",
            state="COMPLETE",
        )

        results_a = get_disagreements("ORG-A")
        results_b = get_disagreements("ORG-B")

        self.assertFalse(
            any(
                item["record_id"] == "REC-PRIVATE-B"
                for item in results_a
            )
        )

        self.assertTrue(
            any(
                item["record_id"] == "REC-PRIVATE-B"
                and item["reason"] == "MISSING_IN_B"
                for item in results_b
            )
        )


class DisagreementsAPITests(TestCase):

    @classmethod
    def setUpTestData(cls):
        Location.objects.create(
            location_id="API-LOC-A",
            org_id="ORG-A",
            location_name="API Test A",
        )

        Location.objects.create(
            location_id="API-LOC-B",
            org_id="ORG-B",
            location_name="API Test B",
        )

        for record_id, location_id, total in [
            ("API-REC-1", "API-LOC-A", "100.00"),
            ("API-REC-2", "API-LOC-A", "300.00"),
            ("API-REC-3", "API-LOC-B", "900.00"),
        ]:
            SystemARecord.objects.create(
                record_id=record_id,
                location_id=location_id,
                event_date="2026-01-01",
                category_code="TEST",
                actor_id="TEST",
                base_value=total,
                adjustment="0.00",
                total_value=total,
                state="COMPLETE",
            )

        for entry_id, ref, location_id, value in [
            ("API-E1", "API-REC-1", "API-LOC-A", "50.00"),
            ("API-E2", "API-REC-2", "API-LOC-A", "200.00"),
        ]:
            SystemBEntry.objects.create(
                entry_id=entry_id,
                record_ref=ref,
                normalized_record_ref=ref,
                location_id=location_id,
                recorded_on="2026-01-01",
                value=value,
                raw_value=value,
                label="API Test",
            )

    def test_org_parameter_required(self):
        response = self.client.get("/api/disagreements/")
        self.assertEqual(response.status_code, 400)

    def test_api_tenant_filtering(self):
        response = self.client.get(
            "/api/disagreements/?org=ORG-A"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["count"], 2)

        record_ids = [
            item["record_id"]
            for item in data["results"]
        ]
        self.assertNotIn("API-REC-3", record_ids)

    def test_reason_filtering(self):
        response = self.client.get(
            "/api/disagreements/",
            {
                "org": "ORG-A",
                "reason": "VALUE_MISMATCH",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 2)

    def test_sort_by_value_descending(self):
        response = self.client.get(
            "/api/disagreements/",
            {
                "org": "ORG-A",
                "sort": "-value",
            },
        )

        self.assertEqual(response.status_code, 200)

        record_ids = [
            item["record_id"]
            for item in response.json()["results"]
        ]

        self.assertEqual(
            record_ids,
            ["API-REC-2", "API-REC-1"],
        )

    def test_invalid_sort_field(self):
        response = self.client.get(
            "/api/disagreements/",
            {
                "org": "ORG-A",
                "sort": "-unknown",
            },
        )

        self.assertEqual(response.status_code, 400)
