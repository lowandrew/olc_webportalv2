from django import forms


class DataRequestForm(forms.Form):
    seqids = forms.CharField(max_length=2048)
