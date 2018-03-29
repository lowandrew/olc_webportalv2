from django.test import TestCase
import os
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0, parentdir)
from views import upload_samples


class SampleTestCase(TestCase):
    # def setUp(self):
        # Sample.objects.create(title='FakeSample')

    def test_things(self):
        # fake_sample = Sample.objects.get(title='FakeSample')
        self.assertEqual(True, True)

