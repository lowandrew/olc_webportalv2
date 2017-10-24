import pandas as pd
import glob
import csv

from subprocess import Popen
from background_task import background

from .models import Project, GenesipprResults, SendsketchResults


@background(schedule=2)
def run_sendsketch(read1, read2, proj_pk, file_path):
    print('\nrun_sendsketch() called successfully for project ID {}'.format(proj_pk))

    output_filename = '{0}/project_{1}_sendsketch_results.txt'.format(file_path, proj_pk)

    # Run Genesippr
    cmd = 'docker exec ' \
          'olcwebportalv2_bbmap ' \
          'sendsketch.sh ' \
          'in=/sequences/{0} ' \
          'in2=/sequences/{1} ' \
          'out=/sequences/{2} ' \
          'reads=400k'.format(read1, read2, output_filename)

    try:
        p = Popen(cmd, shell=True)
        p.communicate()  # wait until the script completes before resuming the code
    except:
        print('sendsketch.sh failed to execute command.')
        quit()

    sendsketch_result_path = 'olc_webportalv2/media/{}'.format(output_filename)

    # try:
    read_sendsketch_results(sendsketch_result_path, proj_pk=proj_pk)
    # print('Successfully read sendsketch results from {}'.format(sendsketch_result_path))
    Project.objects.filter(pk=proj_pk).update(sendsketch_status="Complete")
    # except:
    #     print('Failed to read sendsketch results from {}'.format(sendsketch_result_path))
    #     Project.objects.filter(pk=proj_pk).update(sendsketch_status="Error")

    print('\nsendsketch.sh container actions complete')



@background(schedule=5)
def run_genesippr(file_path, proj_pk):

    print('\nrun_genesippr() called successfully for project ID {}'.format(proj_pk))

    # Run Genesippr
    cmd = 'docker exec ' \
          'genesipprv2 ' \
          'python3 ' \
          'geneSipprV2/sipprverse/method.py ' \
          '/sequences/{0} ' \
          '-t /targets ' \
          '-s /sequences/{0}'.format(file_path)

    try:
        p = Popen(cmd, shell=True)
        p.communicate()  # wait until the script completes before resuming the code
    except:
        print('GenesipprV2 failed to execute command.')
        quit()

    print('\nGenesipprV2 container actions complete')

    genesippr_result_path = glob.glob('olc_webportalv2/media/{}/reports/genesippr.csv'.format(file_path))
    genesippr_result_path = genesippr_result_path[0]

    print('\nAttempting to read ' + genesippr_result_path)
    try:
        read_genesippr_results(genesippr_result_path, proj_pk)
        Project.objects.filter(pk=proj_pk).update(genesippr_status="Complete")
        print('\nReading genesippr results complete.')
    except:
        print('\nReading genesippr results failed.')


def read_genesippr_results(genesippr_result_path, proj_pk):
    # TODO: Use pandas instead of this hack (see read_sendsketch_results())
    with open(genesippr_result_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=',')
        # header = next(reader)
        for row in reader:
            GenesipprResults.objects.filter(project=Project.objects.get(id=proj_pk)).\
                update(strain=str(row[0]),
                       genus=str(row[1],))


def read_sendsketch_results(sendsketch_result_path, proj_pk):
    # Read raw result file
    df = pd.read_csv(sendsketch_result_path, sep='\t', skiprows=2)

    # Sort by ANI
    df = df.sort_values('ANI', ascending=False)

    # Pull records into dictionary
    df_records = df.to_dict('records')

    # Create list of model instances for bulk create with a list comprehension
    model_instances = [SendsketchResults(
        project=Project.objects.get(id=proj_pk),
        wkid=record['WKID'],
        kid=record['KID'],
        ani=record['ANI'],
        complt=record['Complt'],
        contam=record['Contam'],
        matches=record['Matches'],
        unique=record['Unique'],
        nohit=record['noHit'],
        taxid=record['TaxID'],
        gsize=record['gSize'],
        gseqs=record['gSeqs'],
        taxname=record['taxName']
    ) for record in df_records]

    # Update model
    SendsketchResults.objects.bulk_create(model_instances)


