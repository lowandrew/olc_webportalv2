from django import forms
from Bio import SeqIO
from io import StringIO
import re
from olc_webportalv2.metadata.models import SequenceData


class GeneSeekrForm(forms.Form):
    seqids = forms.CharField(max_length=100000, widget=forms.Textarea, label='')
    query_sequence = forms.CharField(max_length=10000, widget=forms.Textarea, label='', required=False)
    query_file = forms.FileField(label='', required=False)

    def clean(self):
        super().clean()
        seqid_input = self.cleaned_data.get('seqids')
        query_sequence = self.cleaned_data.get('query_sequence')
        query_file = self.cleaned_data.get('query_file')

        # Check that SEQIDs specified are in valid SEQID format.
        seqid_list = seqid_input.split()
        bad_seqids = list()
        for seqid in seqid_list:
            if not re.match('\d{4}-[A-Z]+-\d{4}', seqid):
                bad_seqids.append(seqid)
        if len(bad_seqids) > 0:
            raise forms.ValidationError('One or more of the SEQIDs you entered was not formatted correctly. '
                                        'Correct format is YYYY-LAB-####. Also, ensure that you have entered one '
                                        'SEQID per line.\n'
                                        'Invalid SEQIDs: {}'.format(bad_seqids))
        # Also check that SEQIDs are present in our database of SEQIDs
        sequence_data_objects = SequenceData.objects.filter()
        seqids_in_database = list()
        bad_seqids = list()
        for sequence_data in sequence_data_objects:
            seqids_in_database.append(sequence_data.seqid)
        for seqid in seqid_list:
            if seqid not in seqids_in_database:
                bad_seqids.append(seqid)
        if len(bad_seqids) > 0:
            raise forms.ValidationError('One or more of the SEQIDs you entered was not found in our database.\n'
                                        'SEQIDs not found: {}'.format(bad_seqids))

        # TODO: Ensure that input is in valid FASTA format.
        # TODO: Make sure file size isn't greater than 10KB
        # Ensure that query sequence or query file was submitted
        if query_sequence == '' and query_file is None:
            raise forms.ValidationError('No input found! You must submit a FASTA sequence by pasting it into the text '
                                        'box or uploading a FASTA file.')
        elif query_sequence != '' and query_file is not None:
            raise forms.ValidationError('Multiple inputs found! You must submit a FASTA sequence by pasting it into '
                                        'the text box or uploading a FASTA file, but not both.')

        # Check proper FASTA format. Must have at least one sequence, and that must have only A,C,T,G or N
        # Check query sequence, if specified.
        if query_sequence != '':
            num_sequences = 0
            sequences = SeqIO.parse(StringIO(query_sequence), 'fasta')
            valid_bases = set('ACTGN')
            for sequence in sequences:
                num_sequences += 1
                if not set(str(sequence.seq).upper()).issubset(valid_bases):
                    raise forms.ValidationError('Your FASTA sequence contains invalid characters. Sequence should '
                                                'only contain valid nucleotides (A, C, T, G, N).')

            if num_sequences == 0:
                raise forms.ValidationError('Invalid FASTA sequence entered. Correct format is:\n>sequencename\nACTGATCGA')

        # Check query file, if that's what was specified.
        if query_file is not None:
            num_nucleotides = 0
            num_sequences = 0
            sequence_data = query_file.read().decode('utf-8')
            sequences = SeqIO.parse(StringIO(sequence_data), 'fasta')
            valid_bases = set('ACTGN')
            for sequence in sequences:
                num_sequences += 1
                num_nucleotides += len(sequence.seq)
                if not set(str(sequence.seq).upper()).issubset(valid_bases):
                    raise forms.ValidationError('Your FASTA sequence contains invalid characters. Sequence should '
                                                'only contain valid nucleotides (A, C, T, G, N).')

            if num_sequences == 0:
                raise forms.ValidationError('Invalid FASTA sequence entered. Correct format is:\n>sequencename\nACTGATCGA')

            if num_nucleotides > 10000:
                raise forms.ValidationError('FASTA sequence length maximum is 10000 bases. Your input sequence '
                                            'had {} bases.'.format(num_nucleotides))
