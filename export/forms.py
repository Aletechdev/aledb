from django import forms

from ale.models import AleExperiment


class ExportForm(forms.Form):
    experiments = forms.CharField(required=True, strip=True)

    def clean_experiments(self):
        queryset = AleExperiment.objects.all()
        exp_name_str = self.cleaned_data['experiments'].strip()

        if exp_name_str.upper() == 'ALL':
            return queryset

        exp_name_list = map(lambda s: s.strip(), exp_name_str.split(','))

        queryset = queryset.filter(name__in=exp_name_list)

        if not queryset.exists():
            raise forms.ValidationError('No ALE Experiment was found in the database for the given value.')

        return queryset.all()

