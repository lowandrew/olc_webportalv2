import pandas as pd
import pandas_highcharts
import zipfile
import glob
import os

from subprocess import Popen
from background_task import background

from .models import ProjectMulti, Sample, SendsketchResult, GenesipprResults, GenesipprResultsGDCS, \
    GenesipprResultsSixteens, ConFindrResults


@background(schedule=1)
def run_geneseekr(fasta_file, sample_pk):
    print('Running GeneSeekr')
    output_folder = 'olc_webportalv2/media/sample_{}_geneseekr'.format(sample_pk)
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    cmd = 'ln -s -r {fasta} {output_folder}'.format(fasta=os.path.join('olc_webportalv2/media', fasta_file),
                                                    output_folder=output_folder)
    os.system(cmd)

    cmd = 'docker exec ' \
          'olcwebportalv2_geneseekr ' \
          'python -m spadespipeline.GeneSeekr ' \
          '-s /sequences/{output_folder} ' \
          '-t home ' \
          '-r /sequences/{output_folder}'.format(output_folder=os.path.split(output_folder)[-1])
    try:
        p = Popen(cmd, shell=True)
        p.communicate()  # wait until the script completes before resuming the code
        if len(glob.glob(os.path.join(output_folder, '*csv'))) > 0:
            Sample.objects.filter(pk=sample_pk).update(genesippr_status="Complete")
        else:
            Sample.objects.filter(pk=sample_pk).update(genesippr_status="Error")
    except:
        print('GeneSeekr failed to execute command.')
        Sample.objects.filter(pk=sample_pk).update(genesippr_status="Error")
        quit()
    read_geneseekr_results(sample_id=sample_pk,
                           output_folder=output_folder)


@background(schedule=3)
def run_genesippr(project_id):
    print('Running GeneSippr')
    project = ProjectMulti.objects.get(pk=project_id)
    genesippr_dir = 'olc_webportalv2/media/genesippr_{}'.format(project.pk)
    if not os.path.isdir(genesippr_dir):
        os.makedirs(genesippr_dir)
    fastq_count = 0
    for sample in project.samples.all():
        if not sample.file_fasta:
            if sample.genesippr_status != 'Complete':
                fastq_count += 1
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
        if fastq_count > 0:
            p = Popen(cmd, shell=True)
            p.communicate()  # wait until the script completes before resuming the code
            ProjectMulti.objects.filter(pk=project_id).update(gdcs_file=os.path.join(genesippr_dir, 'reports', 'GDCS.csv'))
            ProjectMulti.objects.filter(pk=project_id).update(sixteens_file=os.path.join(genesippr_dir, 'reports', 'sixteens_full.csv'))
            ProjectMulti.objects.filter(pk=project_id).update(genesippr_file=os.path.join(genesippr_dir, 'reports', 'genesippr.csv'))
            ProjectMulti.objects.filter(pk=project_id).update(serosippr_file=os.path.join(genesippr_dir, 'reports', 'serosippr.csv'))
            ProjectMulti.objects.filter(pk=project_id).update(results_created='True')
            genesippr_reports = glob.glob(os.path.join(genesippr_dir, 'reports', '*csv'))
            for sample in project.samples.all():
                if not sample.file_fasta:
                    try:
                        print('Reading GeneSippr result for sample ' + sample.title)
                        read_genesippr_results(genesippr_reports, sample.id)
                        Sample.objects.filter(pk=sample.pk).update(genesippr_status="Complete")
                    except:
                        Sample.objects.filter(pk=sample.pk).update(genesippr_status="Error")
    except:
        print('GenesipprV2 failed to execute command.')
        quit()

    print('\nGenesipprV2 container actions complete')


@background(schedule=2)
def run_sendsketch(read1, read2, sample_pk, file_path):
    print('\nrun_sendsketch() called successfully for sample ID {}'.format(sample_pk))

    output_filename = 'sample_{}_sendsketch_results.txt'.format(sample_pk)
    # Run Sendsketch
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


@background(schedule=2)
def run_confindr(project_id):
    print('Running ConFindr')
    project = ProjectMulti.objects.get(pk=project_id)
    confindr_dir = 'olc_webportalv2/media/confindr_{}'.format(project.pk)
    if not os.path.isdir(confindr_dir):
        os.makedirs(confindr_dir)
    # Create a folder with links to the samples we want to run things on.
    for sample in project.samples.all():
        if sample.confindr_status != 'Complete' and not sample.file_fasta:
            cmd = 'ln -s -r {r1} {confindr_dir}'.format(r1=os.path.join('olc_webportalv2/media', sample.file_R1.name),
                                                        confindr_dir=confindr_dir)
            os.system(cmd)
            cmd = 'ln -s -r {r2} {confindr_dir}'.format(r2=os.path.join('olc_webportalv2/media', sample.file_R2.name),
                                                        confindr_dir=confindr_dir)
            os.system(cmd)

    # Will then need to run ConFindr here using docker exec.
    cmd = 'docker exec ' \
          'olcwebportalv2_confindr ' \
          'confindr.py ' \
          '-i /sequences/confindr_{project_id} ' \
          '-o /sequences/confindr_results_{project_id} ' \
          '-d /home/databases'.format(project_id=project_id)

    try:
        p = Popen(cmd, shell=True)
        p.communicate()  # wait until the script completes before resuming the code
    except:
        print('confindr failed to execute command.')
        quit()
    # Once it's run, need to read the results.
    for sample in project.samples.all():
        if not sample.file_fasta:
            try:
                read_confindr_results(sample_id=sample.id,
                                      confindr_csv='olc_webportalv2/media/confindr_results_{}/confindr_report.csv'.format(project_id))
            except:
                Sample.objects.filter(pk=sample.id).update(confindr_status="Error")
    print('ConFindr run complete')


@background(schedule=2)
def run_sendsketch_fasta(fasta_file, sample_pk):
    print('\nrun_sendsketch() called successfully for sample ID {}'.format(sample_pk))

    output_filename = 'sample_{}_sendsketch_results.txt'.format(sample_pk)
    # Run Sendsketch
    cmd = 'docker exec ' \
          'olcwebportalv2_bbmap ' \
          'sendsketch.sh ' \
          'in=/sequences/{0} ' \
          'out=/sequences/{1} ' \
          'reads=400k ' \
          'overwrite=true'.format(fasta_file, output_filename)

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


def read_geneseekr_results(sample_id, output_folder):
    geneseekr_csv = glob.glob(os.path.join(output_folder, '*csv'))[0]

    gene_presence_dict = dict()
    with open(geneseekr_csv) as infile:
        lines = infile.readlines()
    for line in lines:
        x = line.split()
        gene = x[1].split('_')[0]
        matches = float(x[2])
        gaps = float(x[4])
        length = float(x[7])
        percent_id = 100.0 * ((matches - gaps)/(length))
        if gene.upper() not in gene_presence_dict:
            gene_presence_dict[gene.upper()] = percent_id
    escherichia_genes = ['EAE', 'O26', 'O45', 'O103', 'O111', "O121", 'O145', 'O157', 'VT1', 'VT2', 'VT2F', 'UIDA']
    listeria_genes = ['HLYA', 'IGS', 'INLJ']
    salmonella_genes = ['INVA', 'STN']
    sample_genus = 'Unknown'
    # Figure out what genes are present and at what percent identity.
    for gene in gene_presence_dict:
        if gene.upper() in escherichia_genes:
            sample_genus = 'Escherichia'
        elif gene.upper() in listeria_genes:
            sample_genus = 'Listeria'
        elif gene.upper() in salmonella_genes:
            sample_genus = 'Salmonella'

    model_fields_to_update = ['SEROTYPE', 'O26', 'O45', 'O103',
                              'O111', 'O121', 'O145', 'O157',
                              'UIDA', 'EAE', 'EAE_1', 'VT1', 'VT2', 'VT2F', 'IGS', 'HLYA', 'INLJ', 'INVA', 'STN']
    for field in model_fields_to_update:
        if field not in gene_presence_dict:
            gene_presence_dict[field] = 'N/A'
    sample = Sample.objects.get(id=sample_id)
    GenesipprResults.objects.update_or_create(sample=Sample.objects.get(id=sample_id),
                strain=sample.title,
                genus=sample_genus,
                vt1=gene_presence_dict['VT1'],
                vt2=gene_presence_dict['VT2'],
                vt2f=gene_presence_dict['VT2F'],
                o26=gene_presence_dict['O26'],
                o45=gene_presence_dict['O45'],
                o103=gene_presence_dict['O103'],
                o111=gene_presence_dict['O111'],
                o121=gene_presence_dict['O121'],
                o145=gene_presence_dict['O145'],
                o157=gene_presence_dict['O157'],
                uida=gene_presence_dict['UIDA'],
                eae=gene_presence_dict['EAE'],
                eae_1=gene_presence_dict['EAE_1'],
                igs=gene_presence_dict['IGS'],
                hlya=gene_presence_dict['HLYA'],
                inlj=gene_presence_dict['INLJ'],
                inva=gene_presence_dict['INVA'],
                stn=gene_presence_dict['STN'])
    GenesipprResultsGDCS.objects.update_or_create(sample=Sample.objects.get(id=sample_id),
                                                  strain=sample.title,
                                                  genus='GDCS analysis not available for FASTA files.')
    GenesipprResultsSixteens.objects.update_or_create(sample=Sample.objects.get(id=sample_id),
                                                      strain=sample.title,
                                                      genus='16S analysis not available for FASTA files.')


def read_confindr_results(sample_id, confindr_csv):
    sample = Sample.objects.get(pk=sample_id)
    df = pd.read_csv(confindr_csv)
    df_records = df.to_dict('records')
    for i in range(len(df_records)):
        if sample.title in df_records[i]['Sample']:
            if df_records[i]['Genus'] == 'Error processing sample':
                Sample.objects.filter(pk=sample_id).update(confindr_status="Error")
            else:
                ConFindrResults.objects.update_or_create(sample=Sample.objects.get(pk=sample_id),
                                                         strain=df_records[i]['Sample'],
                                                         genera_present=df_records[i]['Genus'],
                                                         contam_snvs=df_records[i]['NumContamSNVs'],
                                                         contaminated=df_records[i]['ContamStatus'])
                Sample.objects.filter(pk=sample_id).update(confindr_status="Complete")


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

    # Read raw results files - .fillna method added to prevent 'nan' values from populating db
    genesippr_df = pd.read_csv(genesippr_csv).fillna('')
    gdcs_df = pd.read_csv(gdcs_csv).fillna('')
    sixteens_df = pd.read_csv(sixteens_csv).fillna('')

    # Pull records into dictionaries
    genesippr_df_records = genesippr_df.to_dict('records')
    gdcs_df_records = gdcs_df.to_dict('records')
    sixteens_df_records = sixteens_df.to_dict('records')

    # Parse O45, O103, etc. for serotype

    sample = Sample.objects.get(id=proj_pk)
    # genesippr.csv
    for i in range(len(genesippr_df_records)):
        if genesippr_df_records[i]['Strain'] in sample.title:
            serotype = 'N/A'
            for key, value in genesippr_df_records[i].items():
                if key[0][0] == 'O':
                    if value == '':
                        pass
                    else:
                        serotype = key
            GenesipprResults.objects.update_or_create(sample=Sample.objects.get(id=proj_pk),
                strain=sample.title,
                genus=genesippr_df_records[i]['Genus'],
                vt1=genesippr_df_records[i]['VT1'],
                vt2=genesippr_df_records[i]['VT2'],
                vt2f=genesippr_df_records[i]['VT2f'],
                serotype=serotype,
                o26=genesippr_df_records[i]['O26'],
                o45=genesippr_df_records[i]['O45'],
                o103=genesippr_df_records[i]['O103'],
                o111=genesippr_df_records[i]['O111'],
                o121=genesippr_df_records[i]['O121'],
                o145=genesippr_df_records[i]['O145'],
                o157=genesippr_df_records[i]['O157'],
                uida=genesippr_df_records[i]['uidA'],
                eae=genesippr_df_records[i]['eae'],
                eae_1=genesippr_df_records[i]['eae_1'],
                igs=genesippr_df_records[i]['IGS'],
                hlya=genesippr_df_records[i]['hlyA'],
                inlj=genesippr_df_records[i]['inlJ'],
                inva=genesippr_df_records[i]['invA'],
                stn=genesippr_df_records[i]['stn'])

    # GDCS.csv
    for i in range(len(gdcs_df_records)):
        if gdcs_df_records[i]['Strain'] in sample.title:
            GenesipprResultsGDCS.objects.update_or_create(sample=Sample.objects.get(id=proj_pk),
                strain=gdcs_df_records[i]['Strain'],
                genus=gdcs_df_records[i]['Genus'],
                matches=gdcs_df_records[i]['Matches'],
                meancoverage=gdcs_df_records[i]['MeanCoverage'],
                passfail=gdcs_df_records[i]['Pass/Fail'])

    # sixteens_full.csv
    for i in range(len(sixteens_df_records)):
        if sixteens_df_records[i]['Strain'] in sample.title:
            GenesipprResultsSixteens.objects.update_or_create(sample=Sample.objects.get(id=proj_pk),
                strain=sixteens_df_records[i]['Strain'],
                gene=sixteens_df_records[i]['Gene'],
                percentidentity=sixteens_df_records[i]['PercentIdentity'],
                genus=sixteens_df_records[i]['Genus'],
                foldcoverage=sixteens_df_records[i]['FoldCoverage'])