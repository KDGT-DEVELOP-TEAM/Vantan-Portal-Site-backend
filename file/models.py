import uuid
from django.db import models


class File(models.Model):
    # idをuuidで指定
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey('user_management.Users', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    consent_publication = models.BooleanField(default=False)
    storage_key = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title