from django.db import models
from mtfu.auth_user.models import Tenant


class File(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=False, null=False)
    location = models.CharField(max_length=100, blank=False, null=False)
    expire_at = models.DateTimeField(blank=True, null=True)
    is_public = models.BooleanField(default=False)
    resource = models.CharField(max_length=100, blank=True, null=True)
    resource_id = models.IntegerField(blank=True, null=True)
    delete_flg = models.BooleanField(default=False)

    class Meta:
        db_table = "file"
        unique_together = ("tenant", "name", "resource", "resource_id")
