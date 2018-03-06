from django import forms
from .models import ProjectMulti


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
        self.fields['description'].widget.attrs.update({'placeholder': 'Enter a brief project description (optional)'})

    class Meta:
        model = ProjectMulti
        fields = ('project_title',
                  'description',)


class JobForm(forms.Form):
     JOB_CHOICES = (
         ('genesipprv2', 'GeneSipprV2'),
         ('sendsketch', 'sendsketch'),
     )

     jobs = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=JOB_CHOICES)

# class SampleForm(forms.Form):
#     files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
