
from django.db import models


class Location(models.Model):
    location_id = models.CharField(max_length=30, primary_key=True)
    org_id = models.CharField(max_length=30, db_index=True)
    location_name = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.location_id} ({self.org_id})"


class SystemARecord(models.Model):
    record_id = models.CharField(max_length=50, primary_key=True)
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="system_a_records",
    )
    event_date = models.DateField()
    category_code = models.CharField(max_length=50)
    actor_id = models.CharField(max_length=50)
    base_value = models.DecimalField(max_digits=15, decimal_places=2)
    adjustment = models.DecimalField(max_digits=15, decimal_places=2)
    total_value = models.DecimalField(max_digits=15, decimal_places=2)
    state = models.CharField(max_length=50)

    def __str__(self):
        return self.record_id


class SystemBEntry(models.Model):
    entry_id = models.CharField(max_length=50, primary_key=True)

    # Preserve the original CSV reference exactly.
    record_ref = models.CharField(max_length=100)

    # Store the cleaned reference separately.
    normalized_record_ref = models.CharField(
        max_length=50,
        db_index=True,
        blank=True,
    )

    # Preserve the location ID even when it is invalid.
    location_id = models.CharField(max_length=30, db_index=True)

    recorded_on = models.DateField(null=True, blank=True)

    # A blank amount must remain NULL, never zero.
    value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # Preserve the original amount string.
    raw_value = models.CharField(max_length=100, blank=True)

    label = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.entry_id
