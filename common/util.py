from common.constants import REQUEST_ALL


def get_ale_experiment_selector(ale_experiment_id, reseq_query):

    if ale_experiment_id is None or ale_experiment_id == REQUEST_ALL:

        return reseq_query

    else:

        return reseq_query.filter(tech_rep__isolate__flask__ale_id__ale_experiment=ale_experiment_id)


def get_ale_number_selector(ale_id, reseq_query):

    if ale_id is None or ale_id == REQUEST_ALL:

        return reseq_query

    else:

        return reseq_query.filter(tech_rep__isolate__flask__ale_id__ale_id=ale_id)

