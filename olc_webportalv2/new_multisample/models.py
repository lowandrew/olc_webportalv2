from django.db import models
from olc_webportalv2.users.models import User
import os
from django.core.exceptions import ValidationError

# Create your models here.
# TODO: Add some __str__ dunders so that my admin panel gets  nicer names for things


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


class Sample(models.Model):
    project = models.ForeignKey(ProjectMulti, on_delete=models.CASCADE)
    file_R1 = models.FileField(upload_to='', blank=True, validators=[validate_fastq])
    file_R2 = models.FileField(upload_to='', blank=True, validators=[validate_fastq])
    description = models.CharField(max_length=200, blank=True)


class Attachment(models.Model):
    # project = models.ForeignKey(ProjectMulti, on_delete=models.CASCADE)
    attachment = models.FileField(upload_to='')
