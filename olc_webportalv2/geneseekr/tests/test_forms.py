from django.test import TestCase, Client
from django.urls import reverse
from olc_webportalv2.geneseekr.forms import ParsnpForm, GeneSeekrForm
from olc_webportalv2.metadata.models import SequenceData
from olc_webportalv2.users.models import User
from django.core.files.uploadedfile import SimpleUploadedFile


class FormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create(username='TestUser')
        user.set_password('password')
        user.save()
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
