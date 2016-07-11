from ale.models import Filter


__author__ = 'Denny Gosting, Patrick Phaneuf'


def get_filter_settings(ale_experiment_id):

    filter_queryset = Filter.objects.filter(ale_experiment_id=ale_experiment_id)

    if len(filter_queryset) is 0:
        return Filter()

    filter_settings = filter_queryset[0]  # Since there's only one filter setting per experiment.

    return filter_settings
