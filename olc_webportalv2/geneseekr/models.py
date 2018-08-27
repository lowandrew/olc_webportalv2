from django.db import models
from django.contrib.postgres.fields import ArrayField
from olc_webportalv2.users.models import User


# Create your models here.
class GeneSeekrRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seqids = ArrayField(models.CharField(max_length=24), blank=True, default=[])
    missing_seqids = ArrayField(models.CharField(max_length=24), blank=True, default=[])
    query_sequence = models.CharField(max_length=10000, blank=True)
    status = models.CharField(max_length=64, default='Unprocessed')
    download_link = models.CharField(max_length=256, blank=True)
    created_at = models.DateField(auto_now_add=True)
    geneseekr_type = models.CharField(max_length=48, default='BLASTN')


class AzureGeneSeekrTask(models.Model):
    geneseekr_request = models.ForeignKey(GeneSeekrRequest, on_delete=models.CASCADE, related_name='azuretask')
    exit_code_file = models.CharField(max_length=256)
