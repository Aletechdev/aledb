from django.core.management import BaseCommand
from builder.ale_experiment import create_ale_experiment_or_insert_flasks


class Command(BaseCommand):

    help = "This function is used to create an experiment"

    def add_arguments(self, parser):

        parser.add_argument('--path', action='store', dest='path', default=True,
                            help='Path to you experiment directory')
        parser.add_argument('--user', action='store', dest='user', default=True,
                            help='User\'s name who created the experiment')
        parser.add_argument('--name', action='store', dest='name', default=True,
                            help='Experiemnt name')

    def handle(self, *args, **options):

        path = options['path']

        user = options['user']

        name = options['name']

        create_ale_experiment_or_insert_flasks(path, user, name)
