# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-03-16 17:05
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.postgres.fields.hstore
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunSQL("CREATE EXTENSION IF NOT EXISTS hstore"),
        migrations.CreateModel(
            name='ConFindrResults',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('strain', models.CharField(default='N/A', max_length=256)),
                ('genera_present', models.CharField(default='N/A', max_length=256)),
                ('contam_snvs', models.CharField(default='N/A', max_length=256)),
                ('contaminated', models.CharField(default='N/A', max_length=256)),
            ],
            options={
                'verbose_name_plural': 'Confindr Results',
            },
        ),
        migrations.CreateModel(
            name='GenesipprResults',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('strain', models.CharField(default='N/A', max_length=256)),
                ('genus', models.CharField(default='N/A', max_length=256)),
                ('serotype', models.CharField(default='N/A', max_length=256)),
                ('o26', models.CharField(default='N/A', max_length=256)),
                ('o45', models.CharField(default='N/A', max_length=256)),
                ('o103', models.CharField(default='N/A', max_length=256)),
                ('o111', models.CharField(default='N/A', max_length=256)),
                ('o121', models.CharField(default='N/A', max_length=256)),
                ('o145', models.CharField(default='N/A', max_length=256)),
                ('o157', models.CharField(default='N/A', max_length=256)),
                ('uida', models.CharField(default='N/A', max_length=256)),
                ('eae', models.CharField(default='N/A', max_length=256)),
                ('eae_1', models.CharField(default='N/A', max_length=256)),
                ('vt1', models.CharField(default='N/A', max_length=256)),
                ('vt2', models.CharField(default='N/A', max_length=256)),
                ('vt2f', models.CharField(default='N/A', max_length=256)),
                ('igs', models.CharField(default='N/A', max_length=256)),
                ('hlya', models.CharField(default='N/A', max_length=256)),
                ('inlj', models.CharField(default='N/A', max_length=256)),
                ('inva', models.CharField(default='N/A', max_length=256)),
                ('stn', models.CharField(default='N/A', max_length=256)),
            ],
            options={
                'verbose_name_plural': 'Genesippr Results',
            },
        ),
        migrations.CreateModel(
            name='GenesipprResultsGDCS',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('strain', models.CharField(default='N/A', max_length=256)),
                ('genus', models.CharField(default='N/A', max_length=256)),
                ('matches', models.CharField(default='N/A', max_length=256)),
                ('meancoverage', models.CharField(default='N/A', max_length=128)),
                ('passfail', models.CharField(default='N/A', max_length=16)),
                ('allele_dict', django.contrib.postgres.fields.hstore.HStoreField()),
            ],
            options={
                'verbose_name_plural': 'GDCS Results',
            },
        ),
        migrations.CreateModel(
            name='GenesipprResultsSerosippr',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name_plural': 'Serosippr Results',
            },
        ),
        migrations.CreateModel(
            name='GenesipprResultsSixteens',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('strain', models.CharField(default='N/A', max_length=256)),
                ('gene', models.CharField(default='N/A', max_length=256)),
                ('percentidentity', models.CharField(default='N/A', max_length=256)),
                ('genus', models.CharField(default='N/A', max_length=256)),
                ('foldcoverage', models.CharField(default='N/A', max_length=256)),
            ],
            options={
                'verbose_name_plural': 'SixteenS Results',
            },
        ),
        migrations.CreateModel(
            name='GenomeQamlResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('predicted_class', models.CharField(default='N/A', max_length=128)),
                ('percent_fail', models.CharField(default='N/A', max_length=128)),
                ('percent_pass', models.CharField(default='N/A', max_length=128)),
                ('percent_reference', models.CharField(default='N/A', max_length=118)),
            ],
            options={
                'verbose_name_plural': 'GenomeQAML Results',
            },
        ),
        migrations.CreateModel(
            name='ProjectMulti',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_title', models.CharField(max_length=256)),
                ('description', models.CharField(blank=True, max_length=200)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('gdcs_file', models.CharField(default='', max_length=256)),
                ('genesippr_file', models.CharField(default='', max_length=256)),
                ('serosippr_file', models.CharField(default='', max_length=256)),
                ('sixteens_file', models.CharField(default='', max_length=256)),
                ('results_created', models.CharField(default='False', max_length=10)),
                ('forward_id', models.CharField(default='_R1', max_length=256)),
                ('reverse_id', models.CharField(default='_R2', max_length=256)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Sample',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_R1', models.FileField(blank=True, upload_to='%Y%m%d%s')),
                ('file_R2', models.FileField(blank=True, upload_to='%Y%m%d%s')),
                ('file_fasta', models.FileField(blank=True, upload_to='%Y%m%d%s')),
                ('title', models.CharField(blank=True, max_length=200)),
                ('genesippr_status', models.CharField(default='Unprocessed', max_length=128)),
                ('sendsketch_status', models.CharField(default='Unprocessed', max_length=128)),
                ('confindr_status', models.CharField(default='Unprocessed', max_length=128)),
                ('genomeqaml_status', models.CharField(default='Unprocessed', max_length=128)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='samples', to='new_multisample.ProjectMulti')),
            ],
        ),
        migrations.CreateModel(
            name='SendsketchResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank', models.CharField(default='N/A', max_length=8)),
                ('wkid', models.CharField(default='N/A', max_length=256)),
                ('kid', models.CharField(default='N/A', max_length=256)),
                ('ani', models.CharField(default='N/A', max_length=256)),
                ('complt', models.CharField(default='N/A', max_length=256)),
                ('contam', models.CharField(default='N/A', max_length=256)),
                ('matches', models.CharField(default='N/A', max_length=256)),
                ('unique', models.CharField(default='N/A', max_length=256)),
                ('nohit', models.CharField(default='N/A', max_length=256)),
                ('taxid', models.CharField(default='N/A', max_length=256)),
                ('gsize', models.CharField(default='N/A', max_length=256)),
                ('gseqs', models.CharField(default='N/A', max_length=256)),
                ('taxname', models.CharField(default='N/A', max_length=256)),
                ('sample', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='new_multisample.Sample')),
            ],
            options={
                'verbose_name_plural': 'Sendsketch Results',
            },
        ),
        migrations.AddField(
            model_name='genomeqamlresult',
            name='sample',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='genomeqaml_result', to='new_multisample.Sample'),
        ),
        migrations.AddField(
            model_name='genesipprresultssixteens',
            name='sample',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sixteens_results', to='new_multisample.Sample'),
        ),
        migrations.AddField(
            model_name='genesipprresultsserosippr',
            name='sample',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='new_multisample.Sample'),
        ),
        migrations.AddField(
            model_name='genesipprresultsgdcs',
            name='sample',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gdcs_results', to='new_multisample.Sample'),
        ),
        migrations.AddField(
            model_name='genesipprresults',
            name='sample',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='genesippr_results', to='new_multisample.Sample'),
        ),
        migrations.AddField(
            model_name='confindrresults',
            name='sample',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='confindr_results', to='new_multisample.Sample'),
        ),
    ]
