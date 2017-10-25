import pandas as pd
import glob

from subprocess import Popen
from background_task import background

from .models import Project, \
    GenesipprResults, \
    GenesipprResultsGDCS, \
    GenesipprResultsSixteens, \
    SendsketchResults


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

    genesippr_reports = glob.glob('olc_webportalv2/media/{}/reports/*.csv'.format(file_path))

    print('\nAttempting to read the following:')
    for report in genesippr_reports:
        print(report)
    try:
        read_genesippr_results(genesippr_reports, proj_pk)
        Project.objects.filter(pk=proj_pk).update(genesippr_status="Complete")
        print('\nReading genesippr results complete.')
    except:
        print('\nReading genesippr results failed.')


def read_genesippr_results(genesippr_reports, proj_pk):
    # Pull out reports
    genesippr_csv = gdcs_csv = serosippr_csv = sixteens_csv = None

    # Grab reports from glob list
    for report in genesippr_reports:
        if 'genesippr.csv' in report:
            genesippr_csv = report
        elif 'GDCS.csv' in report:
            gdcs_csv = report
        elif 'serosippr.csv' in report:
            serosippr_csv = report
        elif 'sixteens_full' in report:
            sixteens_csv = report

    # Read raw results files
    genesippr_df = pd.read_csv(genesippr_csv)
    gdcs_df = pd.read_csv(gdcs_csv)
    sixteens_df = pd.read_csv(sixteens_csv)

    # Pull records into dictionaries
    genesippr_df_records = genesippr_df.to_dict('records')
    gdcs_df_records = gdcs_df.to_dict('records')
    sixteens_df_records = sixteens_df.to_dict('records')

    # Parse O45, O103, etc. for serotype
    serotype = 'N/A'
    for key, value in genesippr_df_records[0].items():
        if key[0][0] == 'O':
            if pd.isnull(value):
                pass
            else:
                serotype = key

    # genesippr.csv
    GenesipprResults.objects.filter(project=Project.objects.get(id=proj_pk)).update(
        strain=genesippr_df_records[0]['Strain'],
        genus=genesippr_df_records[0]['Genus'],
        vt1=genesippr_df_records[0]['VT1'],
        vt2=genesippr_df_records[0]['VT2'],
        vt2f=genesippr_df_records[0]['VT2f'],
        serotype=serotype,
        o26=genesippr_df_records[0]['O26'],
        o45=genesippr_df_records[0]['O45'],
        o103=genesippr_df_records[0]['O103'],
        o111=genesippr_df_records[0]['O111'],
        o121=genesippr_df_records[0]['O121'],
        o145=genesippr_df_records[0]['O145'],
        o157=genesippr_df_records[0]['O157'],
        uida=genesippr_df_records[0]['uidA'],
        eae=genesippr_df_records[0]['eae'],
        eae_1=genesippr_df_records[0]['eae_1'],
        igs=genesippr_df_records[0]['IGS'],
        hyla=genesippr_df_records[0]['hylA'],
        inlj=genesippr_df_records[0]['inlJ'],
        inva=genesippr_df_records[0]['invA'],
        stn=genesippr_df_records[0]['stn']
    )

    # GDCS.csv
    GenesipprResultsGDCS.objects.filter(project=Project.objects.get(id=proj_pk)).update(
        strain=gdcs_df_records[0]['Strain'],
        genus=gdcs_df_records[0]['Genus'],
        matches=gdcs_df_records[0]['Matches'],
    )

    # sixteens_full.csv
    GenesipprResultsSixteens.objects.filter(project=Project.objects.get(id=proj_pk)).update(
        strain=sixteens_df_records[0]['Strain'],
        gene=sixteens_df_records[0]['Gene'],
        percentidentity=sixteens_df_records[0]['PercentIdentity'],
        genus=sixteens_df_records[0]['Genus'],
        foldcoverage=sixteens_df_records[0]['FoldCoverage'],
    )


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


