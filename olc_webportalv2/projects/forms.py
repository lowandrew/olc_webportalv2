from django import forms
from .models import Project


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BootstrapModelForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class ProjectForm(BootstrapModelForm):
    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        self.fields['project_title'].widget.attrs.update({'placeholder': 'Enter a project title'})
        self.fields['requested_jobs'].widget.attrs.update({'class': 'btn btn-success'})


    class Meta:
        model = Project
        fields = ('project_title',
                  'file_R1',
                  'file_R2',
                  'requested_jobs')
