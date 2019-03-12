from django.core.management import BaseCommand
from builder.ale_experiment import delete_ale_experiments


class Command(BaseCommand):

    help = "This function is used to delete experiments using their ids."

    def add_arguments(self, parser):
        parser.add_argument('ids', nargs='+', type=int, help='ids of the experiments to delete')

    def handle(self, *args, **options):
        ids = options['ids']
        delete_ale_experiments(ids)