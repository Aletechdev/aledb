from django.core.management import BaseCommand
from bibliome.publication import add_publication_to_experiment


class Command(BaseCommand):

    help = "This function is used to add doi entries experiment(s)."

    def add_arguments(self, parser):
        parser.add_argument('id(s):doi pair', nargs='+', type=str, help='experiment ids associated with this publication')

    def handle(self, *args, **options):
        pairs = options['id(s):doi pair']
        for pair in pairs:
            pair = pair.split(":")
            ids = pair[0].split(",")
            ale_ids = []
            for id in ids:
                if ".." in id:
                    ends = id.split("..")
                    ale_ids = ale_ids + list(range(int(ends[0]), int(ends[1])+1))
                else:
                    ale_ids.append(int(id))
            doi = pair[1]
            add_publication_to_experiment(ale_ids, doi, replace=True)
