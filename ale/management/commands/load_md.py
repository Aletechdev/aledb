from django.core.management import BaseCommand
from metadata.parser import parse_metadata_post_experiment_upload


class Command(BaseCommand):

    help = "This function is used to (re)upload metadata for existing experiments."

    def add_arguments(self, parser):
        parser.add_argument('path_id_pair(s)', nargs='+', type=str, help='Path-aleid-pairs in path:id format')

    def handle(self, *args, **options):
        pairs = options['path_id_pair(s)']
        for pair in pairs:
            path, exp_id = pair.split(':')
            print("Processing", path, ": ", exp_id)
            parse_metadata_post_experiment_upload(path, exp_id)
