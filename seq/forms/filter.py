from django import forms

from ale.models import Filter


# TODO: Add CharField.
class FilterForm(forms.ModelForm):

    # Simply initializes form.
    min_cutoff = forms.IntegerField(min_value=0, max_value=100, required=False, initial=20)
    max_cutoff = forms.IntegerField(min_value=0, max_value=100, required=False, initial=100)

    def has_changed(self):
        return True

    class Meta:
        model = Filter
        fields = ["min_cutoff", "max_cutoff"]