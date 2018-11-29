from django.test import TestCase, Client
from django.urls import reverse
from olc_webportalv2.geneseekr.forms import ParsnpForm, GeneSeekrForm
from olc_webportalv2.metadata.models import SequenceData
from django.core.files.uploadedfile import SimpleUploadedFile


class GeneSeekrFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        sequence_data = SequenceData.objects.create(seqid='2015-SEQ-0711',
                                                    quality='Pass',
                                                    genus='Listeria')
        sequence_data.save()
        sequence_data = SequenceData.objects.create(seqid='2015-SEQ-0712',
                                                    quality='Pass',
                                                    genus='Listeria')
        sequence_data.save()

    def test_valid_geneseekr_form_seqid_input_fasta_text(self):
        form = GeneSeekrForm({
            'seqids': '2015-SEQ-0711 2015-SEQ-0712',
            'query_sequence': '>fasta_name\nATCGACTGACTAGTCA'
        })
        self.assertTrue(form.is_valid())

    def test_valid_geneseekr_form_genus_input_fasta_text(self):
        form = GeneSeekrForm({
            'genus': 'Listeria',
            'query_sequence': '>fasta_name\nATCGACTGACTAGTCA'
        })
        self.assertTrue(form.is_valid())

    def test_valid_geneseekr_form_seqid_input_fasta_file(self):
        with open('olc_webportalv2/geneseekr/tests/good_fasta.fasta', 'rb') as upload_file:
            form = GeneSeekrForm({'seqids': '2015-SEQ-0711 2015-SEQ-0712'}, {'query_file': SimpleUploadedFile(upload_file.name, upload_file.read())})
            self.assertTrue(form.is_valid())

    def test_valid_geneseekr_form_genus_input_fasta_file(self):
        with open('olc_webportalv2/geneseekr/tests/good_fasta.fasta', 'rb') as upload_file:
            form = GeneSeekrForm({'genus': 'Listeria'}, {'query_file': SimpleUploadedFile(upload_file.name, upload_file.read())})
            self.assertTrue(form.is_valid())

    def test_invalid_form_missing_seqid(self):
        form = GeneSeekrForm({
            'seqids': '2222-SEQ-0711 2015-SEQ-0712',
            'query_sequence': '>fasta_name\nATCGACTGACTAGTCA'
        })
        self.assertFalse(form.is_valid())

    def test_invalid_form_bad_fasta_file(self):
        with open('olc_webportalv2/geneseekr/tests/bad_fasta.fasta', 'rb') as upload_file:
            form = GeneSeekrForm({'seqids': '2015-SEQ-0711 2015-SEQ-0712'}, {'query_file': SimpleUploadedFile(upload_file.name, upload_file.read())})
            self.assertFalse(form.is_valid())

    def test_invalid_form_no_sequences_in_genus(self):
        form = GeneSeekrForm({
            'genus': 'TotallyFakeGenus',
            'query_sequence': '>fasta_name\nATCGACTGACTAGTCA'
        })
        self.assertFalse(form.is_valid())

    def test_invalid_form_no_sequences_in_exclude_genus(self):
        form = GeneSeekrForm({
            'genus': 'Listeria',
            'query_sequence': '>fasta_name\nATCGACTGACTAGTCA',
            'everything_but': True,
        })
        self.assertFalse(form.is_valid())

    def test_valid_form_exclude_genus(self):
        form = GeneSeekrForm({
            'genus': 'Salmonella',
            'query_sequence': '>fasta_name\nATCGACTGACTAGTCA',
            'everything_but': True,
        })
        self.assertTrue(form.is_valid())


class ParsnpFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        sequence_data = SequenceData.objects.create(seqid='2015-SEQ-0711',
                                                    quality='Pass',
                                                    genus='Listeria')
        sequence_data.save()
        sequence_data = SequenceData.objects.create(seqid='2015-SEQ-0712',
                                                    quality='Pass',
                                                    genus='Listeria')
        sequence_data.save()

    def test_valid_form(self):
        form = ParsnpForm({
            'seqids': '2015-SEQ-0711 2015-SEQ-0712'
        })
        self.assertTrue(form.is_valid())

    def test_invalid_form_wrong_seqid_regex(self):
        form = ParsnpForm({
            'seqids': '22015-SEQ-0711 2015-SEQ-0712'
        })
        self.assertFalse(form.is_valid())

    def test_invalid_form_wrong_seqid_does_not_exist(self):
        form = ParsnpForm({
            'seqids': '2222-SEQ-0711 2015-SEQ-0712'
        })
        self.assertFalse(form.is_valid())
