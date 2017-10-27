from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from multiselectfield import MultiSelectField
from olc_webportalv2.users.models import User

import datetime
import os


# Validation functions
def validate_fastq(fieldfile):
    filename = os.path.basename(fieldfile.name)
    if filename.endswith('.fastq.gz') or filename.endswith('.fastq'):
        print('File extension for {} confirmed valid'.format(filename))
    else:
        raise ValidationError(
            _('%(file)s does not end with .fastq or .fastq.gz'),
            params={'filename': filename},
        )


class Project(models.Model):
    """
    Main model for storing projects. Each project has a unique ID which is linked to a specific user.
    Job choices must be updated with new modules as they are implemented.
    """
    JOB_CHOICES = (
        ('genesipprv2', 'GenesipprV2'),
        ('sendsketch', 'sendsketch'),
    )

    # user key is pulled from the User model
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project_title = models.CharField(max_length=256)
    description = models.CharField(max_length=200, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    file_R1 = models.FileField(upload_to='', blank=True, validators=[validate_fastq])
    file_R2 = models.FileField(upload_to='', blank=True, validators=[validate_fastq])
    genesippr_status = models.CharField(max_length=128,
                                        default="Unprocessed")
    sendsketch_status = models.CharField(max_length=128,
                                         default="Unprocessed")
    requested_jobs = MultiSelectField(choices=JOB_CHOICES)

    def filename_r1(self):
        return os.path.basename(self.file_R1.name)

    def filename_r2(self):
        return os.path.basename(self.file_R2.name)

    def __str__(self):
        return '{}:{}'.format(self.user, str(self.pk))

    def save(self, *args, **kwargs):
        super(Project, self).save(*args, **kwargs)

        file_R1 = self.file_R1
        file_R2 = self.file_R2

        if file_R1 and file_R2:
            old_R1, old_R2 = self.file_R1.name, self.file_R2.name
            new_R1 = '/'.join(['uploads', self.user.username, datetime.datetime.now().strftime("%Y_%m_%d"),
                               str(self.pk),
                               str(self.file_R1.name)])
            new_R2 = '/'.join(['uploads', self.user.username, datetime.datetime.now().strftime("%Y_%m_%d"),
                               str(self.pk),
                               str(self.file_R2.name)])

            if new_R1 != old_R1 and new_R2 != old_R2:
                self.file_R1.storage.delete(new_R1)
                self.file_R1.storage.save(new_R1, file_R1)
                self.file_R1.name = new_R1
                self.file_R1.close()
                self.file_R1.storage.delete(old_R1)

                self.file_R2.storage.delete(new_R2)
                self.file_R2.storage.save(new_R2, file_R2)
                self.file_R2.name = new_R2
                self.file_R2.close()
                self.file_R2.storage.delete(old_R2)

        super(Project, self).save(*args, **kwargs)

class GenesipprResults(models.Model):
    # For admin panel
    def __str__(self):
        return '{}'.format(self.project)

    # TODO: Accomodate seqID
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    # genesippr.csv
    strain = models.CharField(max_length=256, default="N/A")
    genus = models.CharField(max_length=256, default="N/A")

    # STEC
    serotype = models.CharField(max_length=256, default="N/A")
    o26 = models.CharField(max_length=256, default="N/A")
    o45 = models.CharField(max_length=256, default="N/A")
    o103 = models.CharField(max_length=256, default="N/A")
    o111 = models.CharField(max_length=256, default="N/A")
    o121 = models.CharField(max_length=256, default="N/A")
    o145 = models.CharField(max_length=256, default="N/A")
    o157 = models.CharField(max_length=256, default="N/A")
    uida = models.CharField(max_length=256, default="N/A")
    eae = models.CharField(max_length=256, default="N/A")
    eae_1 = models.CharField(max_length=256, default="N/A")
    vt1 = models.CharField(max_length=256, default="N/A")
    vt2 = models.CharField(max_length=256, default="N/A")
    vt2f = models.CharField(max_length=256, default="N/A")

    # listeria
    igs = models.CharField(max_length=256, default="N/A")
    hyla = models.CharField(max_length=256, default="N/A")
    inlj = models.CharField(max_length=256, default="N/A")

    # salmonella
    inva = models.CharField(max_length=256, default="N/A")
    stn = models.CharField(max_length=256, default="N/A")

    class Meta:
        verbose_name_plural = "Genesippr Results"


class GenesipprResultsSixteens(models.Model):
    class Meta:
        verbose_name_plural = "SixteenS Results"

    def __str__(self):
        return '{}'.format(self.project)

    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    # sixteens_full.csv
    strain = models.CharField(max_length=256, default="N/A")
    gene = models.CharField(max_length=256, default="N/A")
    percentidentity = models.CharField(max_length=256, default="N/A")
    genus = models.CharField(max_length=256, default="N/A")
    foldcoverage = models.CharField(max_length=256, default="N/A")

    @property
    def gi_accession(self):
        # Split by | delimiter, pull second element which should be the GI#
        gi_accession = self.gene.split('|')[1]
        return gi_accession


class GenesipprResultsGDCS(models.Model):
    class Meta:
        verbose_name_plural = "GDCS Results"

    def __str__(self):
        return '{}'.format(self.project)

    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    # GDCS.csv
    strain = models.CharField(max_length=256, default="N/A")
    genus = models.CharField(max_length=256, default="N/A")
    matches = models.CharField(max_length=256, default="N/A")


class GenesipprResultsSerosippr(models.Model):
    class Meta:
        verbose_name_plural = "Serosippr Results"

    def __str__(self):
        return '{}'.format(self.project)

    project = models.ForeignKey(Project, on_delete=models.CASCADE)


class SendsketchResults(models.Model):
    class Meta:
        verbose_name_plural = "Sendsketch Results"

    def __str__(self):
        return '{}'.format(self.project)

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
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


#  Deleting the following functions results in an irritating migration error. Should probably fix this one day...
def generate_path():
    pass


def make_path(instance, filename):
    pass
