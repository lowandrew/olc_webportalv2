from django import forms
from .models import Project


class ProjectForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Project
        fields = ('project_title',
                  'file_R1',
                  'file_R2',
                  'organism',
                  'reference',
                  'type',
                  'requested_jobs')


