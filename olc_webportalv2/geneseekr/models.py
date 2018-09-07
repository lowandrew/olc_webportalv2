from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields import JSONField
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
    # This will hold a dictionary of percent of isolates where gene/sequence was found for each gene:
    # In format (ish) {'gene1': 70, 'gene2: 80}
    geneseekr_results = JSONField(default={}, blank=True, null=True)

    def __str__(self):
        return self.pk


class AzureGeneSeekrTask(models.Model):
    geneseekr_request = models.ForeignKey(GeneSeekrRequest, on_delete=models.CASCADE, related_name='azuretask')
    exit_code_file = models.CharField(max_length=256)


class GeneSeekrDetail(models.Model):
    geneseekr_request = models.ForeignKey(GeneSeekrRequest, on_delete=models.CASCADE, related_name='geneseekrdetail', null=True)
    seqid = models.CharField(max_length=24, default='')
    # Pretty much identical to geneseekr request JSONField, but this one has percent ID for the value instead of percent
    # of times found.
    geneseekr_results = JSONField(default={}, blank=True, null=True)

    def __str__(self):
        return self.seqid
