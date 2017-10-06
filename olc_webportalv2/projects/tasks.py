from subprocess import Popen
from background_task import background
from .models import Project, GenesipprResults
import glob
import csv


@background(schedule=5)
def run_genesippr(file_path, proj_pk):

    Project.objects.filter(id=proj_pk).update(genesippr_status="Processing...")

    print('\nrun_genesippr() called successfully for project ID {}'.format(proj_pk))

    cmd = 'docker exec ' \
          'genesipprv2 ' \
          'python3 ' \
          'geneSipprV2/sipprverse/method.py ' \
          '/sequences/{0} ' \
          '-t /targets ' \
          '-s /sequences/{0}'.format(file_path)

    p = Popen(cmd, shell=True)
    p.communicate()  # wait until the script completes before resuming the code

    print('\nGenesipprV2 container actions complete')

    genesippr_result_path = glob.glob('olc_webportalv2/media/{}/reports/genesippr.csv'.format(file_path))
    genesippr_result_path = genesippr_result_path[0]

    print('Attempting to read ' + genesippr_result_path)
    read_genesippr_results(genesippr_result_path, proj_pk)

    Project.objects.filter(pk=proj_pk).update(genesippr_status="Complete")


def add_genesippr_csv_result(strain, genus, proj_pk):
    """
    Function to retrieve a specific project ID, then update the GenesipprResults model with according data from
    the genesippr.csv report created.
    """
    c = GenesipprResults.objects.get_or_create(project=Project.objects.get(id=proj_pk),
                                               strain=strain,
                                               genus=genus)
    return c


def read_genesippr_results(genesippr_result_path, proj_pk):
    with open(genesippr_result_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=',')
        header = next(reader)
        for row in reader:
            add_genesippr_csv_result(proj_pk=proj_pk,
                                     strain=str(row[0]),
                                     genus=str(row[1]),
                                     )
            # print(row)
            # _, created = GenesipprResults.objects.get_or_create(
            #     strain=row[0],
            #     genus=row[1],
            #     # O26=row[3],
            #     # O45=row[4],
            #     # O103=row[5],
            #     # O111=row[6],
            #     # O121=row[7],
            #     # O145=row[8],
            #     # O157=row[9],
            #     # VT1=row[10],
            #     # VT2=row[11],
            #     # VT2f=row[12],
            #     # uidA=row[13],
            #     # eae=row[14],
            #     # eae_1=row[15],
            #     # IGS=row[16],
            #     # hylA=row[17],
            #     # inlJ=row[18],
            #     # invA=row[19],
            #     # stn=row[20],
            # )
    # except:
    #     print('read_genesippr_results() failed catastrophically')
