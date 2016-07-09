from django import forms

from ale.models import Filter


# TODO: Add CharField.
class FilterForm(forms.ModelForm):

    # Simply initializes form.
    min_cutoff = forms.IntegerField(min_value=0, max_value=100, required=False, initial=20)
    max_cutoff = forms.IntegerField(min_value=0, max_value=100, required=False, initial=100)
    ignored_genes = forms.CharField(widget=forms.Textarea, required=False, initial="")
    ignored_mutations = forms.CharField(widget=forms.Textarea, required=False, initial="")

    def has_changed(self):
        return True

    class Meta:
        model = Filter
        fields = ["min_cutoff", "max_cutoff", "ignored_genes", "ignored_mutations"]
