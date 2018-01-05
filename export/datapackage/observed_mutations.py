import ast
import csv
import io
import os
import tempfile
from collections import OrderedDict

from datapackage import DataPackage, Resource
from django.utils.html import strip_tags

from enrichment.models import EnrichmentMutation
from export.datapackage.utils import get_table_schema
from export.util import FIXED_MUT_TYPE_STR, ENRICH_MUT_TYPE_STR
from filter.models import AleExperimentFilter
from filter.util import _filter_observed_mutations_given_filter_settings
from fixation.models import FixatedMutation
from seq.models import ObservedMutation

observed_mutations_table_schema = get_table_schema('observed_mutations.json')


class ObservedMutationsDataPackageWriter(object):
    def __init__(self, ale_experiments, mutation_type='ALL', package_name=None):
        self.schema = observed_mutations_table_schema
        self.ale_experiments = ale_experiments
        self.mutation_type = mutation_type
        if package_name is not None:
            self.package_name = package_name
        else:
            self.package_name = 'ale-analytics-observed-mutations.zip'

    def query_values(self):
        observed_mutations_queryset = ObservedMutation.objects.none()

        for ale_experiment in self.ale_experiments:

            queryset = ObservedMutation.objects.exclude(
                mutation__gene=''
            ).select_related(
                'sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment',
                'mutation'
            ).filter(
                sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment=ale_experiment,
            )

            queryset = self.apply_mutation_type(queryset, ale_experiment)

            observed_mutations_queryset = observed_mutations_queryset | queryset

        return observed_mutations_queryset.values(
            'mutation__position',
            'mutation__mutation_type',
            'mutation__sequence_change',
            'mutation__gene',
            'mutation__function',
            'mutation__product',
            'mutation__go_process',
            'mutation__go_component',
            'mutation__protein_change',
            'sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__name',
            'sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_id',
            'sequencing_experiment__tech_rep__isolate__flask__flask_number',
            'sequencing_experiment__tech_rep__isolate__isolate_number',
            'sequencing_experiment__tech_rep__tech_rep_number',
        ).all()

    def apply_mutation_type(self, observed_mutations_queryset, ale_experiment):
        if self.mutation_type == FIXED_MUT_TYPE_STR:
            fixed_mut_qryset = FixatedMutation.objects.filter(ale_experiment=ale_experiment)
            fixed_obs_mut_id_list = []
            for fixed_mut in fixed_mut_qryset:
                fixed_obs_mut_id_2d_list = list(ast.literal_eval(fixed_mut.fixed_observed_mutation_series))
                # Just need to get all observed mutations; don't care their about their grouping.
                fixed_obs_mut_id_list += [item for sublist in fixed_obs_mut_id_2d_list for item in sublist]
            return observed_mutations_queryset.filter(id__in=fixed_obs_mut_id_list)
        elif self.mutation_type == ENRICH_MUT_TYPE_STR:
            enrich_mut_qrtset = EnrichmentMutation.objects.filter(ale_experiment=ale_experiment)
            enrich_mut_id_list = []
            for enrich_mut in enrich_mut_qrtset:
                enrich_mut_id_list.append(enrich_mut.mutation_id)
            return observed_mutations_queryset.filter(mutation_id__in=enrich_mut_id_list)
        else:
            return self.apply_filters(observed_mutations_queryset, ale_experiment)

    def apply_filters(self, observed_mutations_queryset, ale_experiment):
        filter_settings = AleExperimentFilter.objects.filter(ale_experiment=ale_experiment).first()
        return _filter_observed_mutations_given_filter_settings(observed_mutations_queryset, filter_settings)

    def get_table(self):
        query = self.query_values()

        rows = []
        for result in query:
            row = OrderedDict()
            rows.append(row)

            row['position'] = format(result['mutation__position'], ',d')
            row['mutation_type'] = result['mutation__mutation_type']
            row['sequence_change'] = result['mutation__sequence_change']
            row['gene'] = result['mutation__gene']
            row['function'] = result.get('mutation__function') or ""
            row['product'] = result.get('mutation__product') or ""
            row['go_process'] = result.get('mutation__go_process') or ""
            row['go_component'] = result.get('mutation__go_component') or ""
            row['protein_change'] = strip_tags(result.get('mutation__protein_change'))
            row['exp_ale_flask_isolate_str'] = self.get_exp_ale_flask_isolate_str(result)

        table = [rows[0].keys()] + [row.values() for row in rows]
        return table

    def get_exp_ale_flask_isolate_str(self, value):
        ale_flask_isolate_str = "A%d F%d I%d R%d" % (
            value['sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_id'],
            value['sequencing_experiment__tech_rep__isolate__flask__flask_number'],
            value['sequencing_experiment__tech_rep__isolate__isolate_number'],
            value['sequencing_experiment__tech_rep__tech_rep_number'],
        )
        return '{ale_experiment_name} {ale_flask_isolate_str}'.format(
            ale_experiment_name=value[
                'sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__name'],
            ale_flask_isolate_str=ale_flask_isolate_str,
        )

    def write_csv(self, table, filepath):
        with open(filepath, 'w') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerows(table)

    def write(self):
        output = io.BytesIO()

        with tempfile.TemporaryDirectory() as base_path:
            package = DataPackage({
                'name': self.package_name,
            }, base_path=base_path)

            csv_filepath = os.path.normpath(os.path.join(base_path, self.schema['path']))
            table = self.get_table()
            self.write_csv(table, csv_filepath)
            package.add_resource(Resource(self.schema).descriptor)

            package.infer()
            try:
                assert package.valid
            except:
                raise Exception(package.errors)

            package.save(output)

        output.seek(0)
        return output
