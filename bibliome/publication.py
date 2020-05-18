from bibliome.models import Publication
from ale.models import AleExperiment


def create_publication(title_str, url_str, ale_exp_pk):
    exp = AleExperiment.objects.get(pk=ale_exp_pk)
    pub = Publication.objects.create(title=title_str, url=url_str, ale_experiment=exp)


def create_publications(title_str, url_str, ale_exp_pk_list):
    for ale_exp_pk in ale_exp_pk_list:
        create_publication(title_str, url_str, ale_exp_pk)


def add_publication_to_experiment(experiment_ids, doi):
    for id in experiment_ids:
        try:
            curr_experiment = AleExperiment.objects.get(ale_id=id)
            curr_doi = curr_experiment.doi
            if len(curr_doi)>0:
                curr_experiment.doi = curr_experiment.doi + " " + doi
            else:
                curr_experiment.doi = doi
            curr_experiment.save()
        except AleExperiment.DoesNotExist:
            continue
