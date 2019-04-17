from bibliome.models import Publication
from ale.models import AleExperiment


def create_publication(title_str, url_str, ale_exp_pk):
    exp = AleExperiment.objects.get(pk=ale_exp_pk)
    pub = Publication.objects.create(title=title_str, url=url_str, ale_experiment=exp)


def create_publications(title_str, url_str, ale_exp_pk_list):
    for ale_exp_pk in ale_exp_pk_list:
        create_publication(title_str, url_str, ale_exp_pk)
