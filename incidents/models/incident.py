from django.db import models


class Incident(models.Model):
    CATEGORY_CHOICES = [
        ('physical', 'Physical Safety'),
        ('digital', 'Digital/Scam'),
        ('weather', 'Weather'),
    ]

    # raw fields
    title       = models.CharField(max_length=255)
    description = models.TextField()
    location    = models.CharField(max_length=100)
    source = models.URLField(max_length=500,default='')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    # enriched fields
    category     = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True)
    severity     = models.IntegerField(default=1)
    is_noise     = models.BooleanField(default=False)
    action_steps = models.TextField(blank=True)

    # enrichment flags
    is_enriched = models.BooleanField(default=False)
    ai_enriched = models.BooleanField(default=False)

    class Meta:
        db_table = 'incidents'
        indexes = [
            models.Index(fields=['is_enriched', 'is_noise']),
            models.Index(fields=['ai_enriched']),
            models.Index(fields=['location']),
        ]

    def __str__(self):
        return f"{self.title} — {self.location}"