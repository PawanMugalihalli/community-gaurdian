from django.db import models
from django.conf import settings


class DigestLog(models.Model):
    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    ai_used      = models.BooleanField()
    result_json  = models.JSONField()

    class Meta:
        db_table = 'digest_logs'

    def __str__(self):
        return f"Digest for {self.user.username} at {self.generated_at}"