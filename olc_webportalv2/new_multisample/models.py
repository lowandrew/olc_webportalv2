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


class Attachment(models.Model):
    # project = models.ForeignKey(ProjectMulti, on_delete=models.CASCADE)
    attachment = models.FileField(upload_to='')


class GenesipprResults(models.Model):
    # For admin panel
    def __str__(self):
        return '{}'.format(self.project)

    # TODO: Accomodate seqID
    project = models.ForeignKey(ProjectMulti, on_delete=models.CASCADE)

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
    hlya = models.CharField(max_length=256, default="N/A")
    inlj = models.CharField(max_length=256, default="N/A")

    # salmonella
    inva = models.CharField(max_length=256, default="N/A")
    stn = models.CharField(max_length=256, default="N/A")

    def inva_number(self):
        return float(self.inva.split('%')[0])

    def uida_number(self):
        return float(self.uida.split('%')[0])

    def vt1_number(self):
        return float(self.vt1.split('%')[0])

    def vt2_number(self):
        return float(self.vt2.split('%')[0])

    def vt2f_number(self):
        return float(self.vt2f.split('%')[0])

    def eae_number(self):
        return float(self.eae.split('%')[0])

    def eae_1_number(self):
        return float(self.eae_1.split('%')[0])

    class Meta:
        verbose_name_plural = "Genesippr Results"


class GenesipprResultsSixteens(models.Model):
    class Meta:
        verbose_name_plural = "SixteenS Results"

    def __str__(self):
        return '{}'.format(self.project)

    project = models.ForeignKey(ProjectMulti, on_delete=models.CASCADE)

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

    project = models.ForeignKey(ProjectMulti, on_delete=models.CASCADE)

    # GDCS.csv
    strain = models.CharField(max_length=256, default="N/A")
    genus = models.CharField(max_length=256, default="N/A")
    matches = models.CharField(max_length=256, default="N/A")
    meancoverage = models.CharField(max_length=128, default="N/A")
    passfail = models.CharField(max_length=16, default="N/A")


class GenesipprResultsSerosippr(models.Model):
    class Meta:
        verbose_name_plural = "Serosippr Results"

    def __str__(self):
        return '{}'.format(self.project)

    project = models.ForeignKey(ProjectMulti, on_delete=models.CASCADE)


class SendsketchResults(models.Model):
    class Meta:
        verbose_name_plural = "Sendsketch Results"

    def __str__(self):
        return 'pk {}: Rank {}: Project {}'.format(self.pk, self.rank, self.project.pk)

    project = models.ForeignKey(ProjectMulti, on_delete=models.CASCADE)
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
