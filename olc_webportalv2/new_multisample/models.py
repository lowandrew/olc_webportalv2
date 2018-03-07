from django.db import models
from olc_webportalv2.users.models import User
import os
from django.core.exceptions import ValidationError
from multiselectfield import MultiSelectField

# Create your models here.


def validate_fastq(fieldfile):
    filename = os.path.basename(fieldfile.name)
    if filename.endswith('.fastq.gz') or filename.endswith('.fastq'):
        print('File extension for {} confirmed valid'.format(filename))
    else:
        raise ValidationError(
            _('%(file)s does not end with .fastq or .fastq.gz'),
            params={'filename': filename},
        )


class ProjectMulti(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project_title = models.CharField(max_length=256)
    description = models.CharField(max_length=200, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    gdcs_file = models.CharField(max_length=256, default='')
    genesippr_file = models.CharField(max_length=256, default='')
    serosippr_file = models.CharField(max_length=256, default='')
    sixteens_file = models.CharField(max_length=256, default='')
    results_created = models.CharField(max_length=10, default='False')

    def __str__(self):
        return self.project_title


class Sample(models.Model):
    project = models.ForeignKey(ProjectMulti, on_delete=models.CASCADE, related_name='samples')
    file_R1 = models.FileField(upload_to='', blank=True)
    file_R2 = models.FileField(upload_to='', blank=True)
    title = models.CharField(max_length=200, blank=True)

    genesippr_status = models.CharField(max_length=128,
                                        default="Unprocessed")
    sendsketch_status = models.CharField(max_length=128,
                                         default="Unprocessed")

    def __str__(self):
        return self.title


class SendsketchResult(models.Model):
    class Meta:
        verbose_name_plural = "Sendsketch Results"

    def __str__(self):
        return 'pk {}: Rank {}: Sample {}'.format(self.pk, self.rank, self.sample.pk)

    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    rank = models.CharField(max_length=8, default='N/A')
    wkid = models.CharField(max_length=256, default='N/A')
    kid = models.CharField(max_length=256, default='N/A')
    ani = models.CharField(max_length=256, default='N/A')
    complt = models.CharField(max_length=256, default='N/A')
    contam = models.CharField(max_length=256, default='N/A')
    matches = models.CharField(max_length=256, default='N/A')
    unique = models.CharField(max_length=256, default='N/A')
    nohit = models.CharField(max_length=256, default='N/A')
    taxid = models.CharField(max_length=256, default='N/A')
    gsize = models.CharField(max_length=256, default='N/A')
    gseqs = models.CharField(max_length=256, default='N/A')
    taxname = models.CharField(max_length=256, default='N/A')
