from django.core.management import BaseCommand
from bibliome.publication import create_publications


class Command(BaseCommand):

    help = "This function is used to create a bibliome entry for experiment(s)."

    def add_arguments(self, parser):
        parser.add_argument('experiment_id(s)', nargs='+', type=int, help='experiment ids associated with this publication')

    def handle(self, *args, **options):
        ids = options['experiment_id(s)']
        title = input("Please enter the publication citation:")
        url = input("Please enter the publication URL:")
        create_publications(title, url, ids)
