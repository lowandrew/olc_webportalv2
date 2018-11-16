import os
import shutil
import datetime
import subprocess
import pandas as pd
from Bio import SeqIO
import multiprocessing
from io import StringIO
from background_task import background
from django.conf import settings
from olc_webportalv2.geneseekr.models import GeneSeekrRequest, GeneSeekrDetail, TopBlastHit

from azure.storage.blob import BlockBlobService
from azure.storage.blob import BlobPermissions


# TODO: Much reworking - blast query sequences against all sequence data, and then just do post-filtering.
# This requires pretty much completely re-writing this :(
@background(schedule=1)
def run_geneseekr(geneseekr_request_pk):
    geneseekr_request = GeneSeekrRequest.objects.get(pk=geneseekr_request_pk)
    try:
        # Running GeneSeekr via batch is not ideal, as it's not really a big job - results should be relatively instant,
        # no need for a 5ish minute delay.

        # Step 1: Make a directory for our things.
        geneseekr_dir = 'olc_webportalv2/media/geneseekr-{}'.format(geneseekr_request_pk)
        if not os.path.isdir(geneseekr_dir):
            os.makedirs(geneseekr_dir)
        # If we're going to run things NOT via batch, all of our files to BLAST against should be stored locally.
        # Need to create links to all those files in our geneseekr_dir.
        sequence_dir = '/sequences'
        # geneseekr_sequence_dir = os.path.join(geneseekr_dir, 'sequences')
        # if not os.path.isdir(geneseekr_sequence_dir):
        #     os.makedirs(geneseekr_sequence_dir)
        # for seqid in geneseekr_request.seqids:
        #     if not os.path.exists(os.path.join(geneseekr_sequence_dir, '{}.fasta'.format(seqid))):
        #         os.symlink(src=os.path.join(sequence_dir, '{}.fasta'.format(seqid)), dst=os.path.join(geneseekr_sequence_dir, '{}.fasta'.format(seqid)))
        # With our symlinks created, also create our query file.
        geneseekr_query_dir = os.path.join(geneseekr_dir, 'targets')
        if not os.path.isdir(geneseekr_query_dir):
            os.makedirs(geneseekr_query_dir)

        with open(os.path.join(geneseekr_query_dir, 'query.tfa'), 'w') as f:
            f.write(geneseekr_request.query_sequence)

        if multiprocessing.cpu_count() > 1:
            threads_to_use = multiprocessing.cpu_count() - 1
        else:
            threads_to_use = 1
        # New way to do things: BLAST the entire database of stuff.
        cmd = 'blastn -query {query_file} -db {mega_fasta} -out {blast_report} ' \
              '-outfmt "6 qseqid sseqid pident length qlen qstart qend sstart send evalue" ' \
              '-num_alignments 50000 ' \
              '-num_threads {threads}'.format(query_file=os.path.join(geneseekr_query_dir, 'query.tfa'),
                                              mega_fasta=os.path.join(sequence_dir, 'mega_fasta.fasta'),
                                              blast_report=os.path.join(geneseekr_dir, 'blast_report.tsv'),
                                              threads=threads_to_use)

        subprocess.call(cmd, shell=True)

        print('Reading geneseekr results')
        get_blast_results(blast_result_file=os.path.join(geneseekr_dir, 'blast_report.tsv'),
                          geneseekr_task=geneseekr_request)
        get_blast_detail(blast_result_file=os.path.join(geneseekr_dir, 'blast_report.tsv'),
                         geneseekr_task=geneseekr_request)
        # TODO: This doesn't work very well when multiple genes get submitted - will need to separate out
        # on a gene by gene basis
        get_blast_top_hits(blast_result_file=os.path.join(geneseekr_dir, 'blast_report.tsv'),
                           geneseekr_task=geneseekr_request)

        # With query and sequence done, can go ahead and call GeneSeekr
        # geneseekr_report_dir = os.path.join(geneseekr_dir, 'reports')
        # cmd = 'GeneSeekr blastn -s {sequences} -t {targets} -r {reports} -n {threads}'.format(sequences=os.path.abspath(geneseekr_sequence_dir),
        #                                                                                       targets=os.path.abspath(geneseekr_query_dir),
        #                                                                                       reports=os.path.abspath(geneseekr_report_dir),
        #                                                                                       threads=threads_to_use)
        # with open(geneseekr_dir + '.txt', 'w') as f:
        #     f.write(cmd)
        # subprocess.call(cmd, shell=True)
        # get_geneseekr_results(geneseekr_result_file='olc_webportalv2/media/geneseekr-{}/reports/geneseekr_blastn.csv'.format(geneseekr_request.pk),
        #                       geneseekr_task=geneseekr_request)
        # get_geneseekr_detail(geneseekr_result_file='olc_webportalv2/media/geneseekr-{}/reports/geneseekr_blastn.csv'.format(geneseekr_request.pk),
        #                      geneseekr_task=geneseekr_request)

        # TODO: Will need to have some sort of printable result file that people can download.
        # print('Uploading result files')
        # shutil.make_archive('olc_webportalv2/media/geneseekr-{}/reports'.format(geneseekr_request.pk),
        #                     'zip',
        #                     'olc_webportalv2/media/geneseekr-{}/reports'.format(geneseekr_request.pk))
        # blob_client = BlockBlobService(account_key=settings.AZURE_ACCOUNT_KEY,
        #                                account_name=settings.AZURE_ACCOUNT_NAME)
        # geneseekr_result_container = 'geneseekr-{}'.format(geneseekr_request.pk)
        # blob_client.create_container(geneseekr_result_container)
        # blob_name = os.path.split('olc_webportalv2/media/geneseekr-{}/reports.zip'.format(geneseekr_request.pk))[1]
        # blob_client.create_blob_from_path(container_name=geneseekr_result_container,
        #                                   blob_name=blob_name,
        #                                   file_path='olc_webportalv2/media/geneseekr-{}/reports.zip'.format(geneseekr_request.pk))
        # Generate an SAS url with read access that users will be able to use to download their sequences.
        # print('Creating Download Link')
        # sas_token = blob_client.generate_container_shared_access_signature(container_name=geneseekr_result_container,
        #                                                                    permission=BlobPermissions.READ,
        #                                                                    expiry=datetime.datetime.utcnow() + datetime.timedelta(days=8))
        # sas_url = blob_client.make_blob_url(container_name=geneseekr_result_container,
        #                                     blob_name=blob_name,
        #                                     sas_token=sas_token)
        # geneseekr_request.download_link = sas_url
        shutil.rmtree('olc_webportalv2/media/geneseekr-{}/'.format(geneseekr_request.pk))
        geneseekr_request.status = 'Complete'
        geneseekr_request.save()
    except:
        geneseekr_request.status = 'Error'
        geneseekr_request.save()


class BlastResult:
    def __init__(self, blast_tabdelimited_line):
        # With my custom output format, headers are:
        # Index 0: query sequence name
        # Index 1: subject sequence name
        # Index 2: percent identity
        # Index 3: alignment length
        # Index 4: query sequence length
        # Index 5: query start position
        # Index 6: query end position
        # Index 7: subject start position
        # Index 8: subject end position
        # Index 9: evalue
        x = blast_tabdelimited_line.rstrip().split()
        self.query_name = x[0]
        self.subject_name = x[1]
        self.seqid = self.subject_name.split('_')[0]  # The fasta that's getting searched will always have SEQID_ as first part of contig name
        self.percent_identity = float(x[2])
        self.alignment_length = int(x[3])
        self.query_sequence_length = int(x[4])
        self.query_start_position = int(x[5])
        self.query_end_position = int(x[6])
        self.subject_start_position = int(x[7])
        self.subject_end_position = int(x[8])
        self.evalue = float(x[9])
        # Also need to have amount of query sequence covered as a percentage.
        self.query_coverage = 100.0 * self.alignment_length/self.query_sequence_length


def get_blast_results(blast_result_file, geneseekr_task):
    # This looks at all sequences we have and finds out how many of our SeqIDs have our query sequence(s).
    # First, parse the query sequence associated with the geneseekr task to find out what our query IDs are.
    query_names = list()
    for query in SeqIO.parse(StringIO(geneseekr_task.query_sequence), 'fasta'):
        query_names.append(query.id)

    # Now get a dictionary initialized where we keep track of which SeqIDs have a hit for each query gene listed.
    # When parsing the BLAST output file, if a gene is found, change the value to True
    gene_hits = dict()
    for query_name in query_names:
        gene_hits[query_name] = dict()
        for seqid in geneseekr_task.seqids:
            gene_hits[query_name][seqid] = False

    # Say anything with 90 percent identity over 90 percent of query length is a hit. # TODO: Make this user defined?
    with open(blast_result_file) as f:
        for result_line in f:
            blast_result = BlastResult(result_line)
            if blast_result.query_coverage > 90 and blast_result.percent_identity > 90:
                gene_hits[blast_result.query_name][blast_result.seqid] = True

    # Now for each gene, total the number of True.
    for query in gene_hits:
        num_hits = 0
        for seqid in gene_hits[query]:
            if gene_hits[query][seqid] is True:
                num_hits += 1
        percent_found = 100 * num_hits/len(geneseekr_task.seqids)
        geneseekr_task.geneseekr_results[query] = percent_found
    geneseekr_task.save()


def get_blast_detail(blast_result_file, geneseekr_task):
    # This method finds the percent ID for each gene for each SeqID
    # First, parse the query sequence associated with the geneseekr task to find out what our query IDs are.
    query_names = list()
    for query in SeqIO.parse(StringIO(geneseekr_task.query_sequence), 'fasta'):
        query_names.append(query.id)

    # Now get a dictionary initialized where we keep track of which SeqIDs have a hit for each query gene listed.
    # When parsing the BLAST output file, if a gene is found, change the value to True
    gene_hits = dict()
    for query_name in query_names:
        gene_hits[query_name] = dict()
        for seqid in geneseekr_task.seqids:
            gene_hits[query_name][seqid] = 0.0

    # Iterate through the blast file to find out the best hit
    with open(blast_result_file) as f:
        for result_line in f:
            blast_result = BlastResult(result_line)
            # Everything gets initialized to zero - only take top hit for each SeqID, which should be first hit in file.
            if gene_hits[blast_result.query_name][blast_result.seqid] == 0:
                gene_hits[blast_result.query_name][blast_result.seqid] = blast_result.percent_identity

    for seqid in geneseekr_task.seqids:
        geneseekr_detail = GeneSeekrDetail.objects.create(geneseekr_request=geneseekr_task,
                                                          seqid=seqid)
        results = dict()
        for query in gene_hits:
            results[query] = gene_hits[query][seqid]
        geneseekr_detail.geneseekr_results = results
        geneseekr_detail.save()


def get_blast_top_hits(blast_result_file, geneseekr_task, num_hits=50):
    # Looks at the top 50 hits for a GeneSeekr request and provides a blast-esque interface for them
    with open(blast_result_file) as f:
        count = 0
        for result_line in f:
            blast_result = BlastResult(result_line)
            top_blast_hit = TopBlastHit(contig_name=blast_result.subject_name,
                                        query_coverage=blast_result.query_coverage,
                                        percent_identity=blast_result.percent_identity,
                                        start_position=blast_result.subject_start_position,
                                        end_position=blast_result.subject_end_position,
                                        e_value=blast_result.evalue,
                                        geneseekr_request=geneseekr_task)
            top_blast_hit.save()
            count += 1
            if count >= num_hits:
                break


