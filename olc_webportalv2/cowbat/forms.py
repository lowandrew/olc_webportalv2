from django import forms
import re


class RunNameForm(forms.Form):
    run_name = forms.CharField(max_length=64)

    def clean_run_name(self):
        run_name = self.cleaned_data['run_name']
        if not re.match('\d{6}_[A-Z]+', run_name):
            raise forms.ValidationError('Invalid run name. Format must be YYMMDD_LAB')
        return run_name
