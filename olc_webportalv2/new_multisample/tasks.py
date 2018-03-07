import pandas as pd
import pandas_highcharts
import zipfile
import glob
import os

from subprocess import Popen
from background_task import background

from .models import ProjectMulti, Sample, SendsketchResult


@background(schedule=3)
def run_genesippr(project_id):
    print('Running GeneSippr')
    project = ProjectMulti.objects.get(pk=project_id)
    genesippr_dir = 'olc_webportalv2/media/genesippr_{}'.format(project.pk)
    if not os.path.isdir(genesippr_dir):
        os.makedirs(genesippr_dir)
    for sample in project.samples.all():
        if sample.genesippr_status != 'Complete':
            cmd = 'ln -s -r {r1} {genesippr_dir}'.format(r1=os.path.join('olc_webportalv2/media', sample.file_R1.name),
                                                         genesippr_dir=genesippr_dir)
            os.system(cmd)
            cmd = 'ln -s -r {r2} {genesippr_dir}'.format(r2=os.path.join('olc_webportalv2/media', sample.file_R2.name),
                                                         genesippr_dir=genesippr_dir)
            os.system(cmd)

    # Run Genesippr
    cmd = 'docker exec ' \
          'olcwebportalv2_genesipprv2 ' \
          'sippr.py ' \
          '/sequences/{0} ' \
          '-t /targets ' \
          '-s /sequences/{0}'.format(os.path.split(genesippr_dir)[-1])

    try:
        p = Popen(cmd, shell=True)
        p.communicate()  # wait until the script completes before resuming the code
        ProjectMulti.objects.filter(pk=project_id).update(gdcs_file=os.path.join(genesippr_dir, 'reports', 'GDCS.csv'))
        ProjectMulti.objects.filter(pk=project_id).update(sixteens_file=os.path.join(genesippr_dir, 'reports', 'sixteens_full.csv'))
        ProjectMulti.objects.filter(pk=project_id).update(genesippr_file=os.path.join(genesippr_dir, 'reports', 'genesippr.csv'))
        ProjectMulti.objects.filter(pk=project_id).update(serosippr_file=os.path.join(genesippr_dir, 'reports', 'serosippr.csv'))
        ProjectMulti.objects.filter(pk=project_id).update(results_created='True')
        for sample in project.samples.all():
            Sample.objects.filter(pk=sample.pk).update(genesippr_status="Complete")
    except:
        print('GenesipprV2 failed to execute command.')
        quit()

    print('\nGenesipprV2 container actions complete')


@background(schedule=2)
def run_sendsketch(read1, read2, sample_pk, file_path):
    print('\nrun_sendsketch() called successfully for sample ID {}'.format(sample_pk))

    output_filename = 'sample_{}_sendsketch_results.txt'.format(sample_pk)
    # Run Genesippr
    cmd = 'docker exec ' \
          'olcwebportalv2_bbmap ' \
          'sendsketch.sh ' \
          'in=/sequences/{0} ' \
          'in2=/sequences/{1} ' \
          'out=/sequences/{2} ' \
          'reads=400k ' \
          'overwrite=true'.format(read1, read2, output_filename)

    try:
        p = Popen(cmd, shell=True)
        p.communicate()  # wait until the script completes before resuming the code
    except:
        print('sendsketch.sh failed to execute command.')
        quit()

    sendsketch_result_path = 'olc_webportalv2/media/{}'.format(output_filename)

    try:
        read_sendsketch_results(sendsketch_result_path, proj_pk=sample_pk)
        print('Successfully read sendsketch results from {}'.format(sendsketch_result_path))
        Sample.objects.filter(pk=sample_pk).update(sendsketch_status="Complete")
    except:
        print('Failed to read sendsketch results from {}'.format(sendsketch_result_path))
        Sample.objects.filter(pk=sample_pk).update(sendsketch_status="Error")

    print('\nsendsketch.sh container actions complete')


def read_sendsketch_results(sendsketch_result_path, proj_pk):
    # Read raw result file
    df = pd.read_csv(sendsketch_result_path, sep='\t', skiprows=2)

    # Drop N/A values
    df = df.dropna(1)

    # Sort by ANI
    df = df.sort_values('ANI', ascending=False)

    # Add ranking column
    df.insert(0, 'Rank', range(1, len(df) + 1))

    # Set Rank to the index
    df.set_index('Rank')

    # Pull records into dictionary
    df_records = df.to_dict('records')

    # Create list of model instances for bulk create with a list comprehension
    for index in range(len(df_records)):
        if df_records[index]['Rank'] != 'N/A':
            to_update = SendsketchResult.objects.create(sample=Sample.objects.get(id=proj_pk))
            to_update.rank = df_records[index]['Rank']
            to_update.wkid = df_records[index]['WKID']
            to_update.kid = df_records[index]['KID']
            to_update.ani = df_records[index]['ANI']
            to_update.complt = df_records[index]['Complt']
            to_update.contam = df_records[index]['Contam']
            to_update.matches = df_records[index]['Matches']
            to_update.unique = df_records[index]['Unique']
            to_update.nohit = df_records[index]['noHit']
            to_update.taxid = df_records[index]['TaxID']
            to_update.gsize = df_records[index]['gSize']
            to_update.gseqs = df_records[index]['gSeqs']
            to_update.taxname = df_records[index]['taxName']
            to_update.save()
