__author__ = 'dgosting'

from django import forms


class IgnoredGenesForm(forms.Form):
    ignored_genes = forms.CharField(widget=forms.Textarea, required=False)