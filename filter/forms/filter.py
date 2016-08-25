from django import forms

from filter.models import AleExperimentFilter

from filter.common import DEFAULT_MUTATION_FREQ_MIN
from filter.common import DEFAULT_MUTATION_FREQ_MAX


# TODO: Add CharField.
class FilterForm(forms.ModelForm):

    # Simply initializes form.
    min_cutoff = forms.IntegerField(min_value=0, max_value=100, required=False, initial=DEFAULT_MUTATION_FREQ_MIN)
    max_cutoff = forms.IntegerField(min_value=0, max_value=100, required=False, initial=DEFAULT_MUTATION_FREQ_MAX)
    ignored_genes = forms.CharField(widget=forms.Textarea, required=False, initial="")
    ignored_mutations = forms.CharField(widget=forms.Textarea, required=False, initial="")

    def has_changed(self):
        return True

    class Meta:
        model = AleExperimentFilter
        fields = ["min_cutoff", "max_cutoff", "ignored_genes"]
