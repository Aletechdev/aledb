from django.core.management import BaseCommand
from builder.ale_experiment import upload_ale_collection


class Command(BaseCommand):

    help = "This function is used to upload collection(s) of experiments."

    def add_arguments(self, parser):
        parser.add_argument('path(s)', nargs='+', type=str, help='Path(s) to you experiment directories')

    def handle(self, *args, **options):
        paths = options['path(s)']
        for path in paths:
            print("Uploading", path)
            upload_ale_collection(path)
