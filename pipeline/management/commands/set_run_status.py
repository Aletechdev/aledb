from django.core.management import BaseCommand, CommandError
from pipeline.models import Run


class Command(BaseCommand):

    help = "Set a pipeline Run's status. Used by the host-side upload script to report the ingest outcome."

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='Run name')
        parser.add_argument('status', type=str, choices=[choice[0] for choice in Run.PIPELINE_RUN_STATUS],
                            help='New status')

    def handle(self, *args, **options):
        updated = Run.objects.filter(name=options['name']).update(status=options['status'])
        if updated == 0:
            raise CommandError("no Run named %r" % options['name'])
        print("Run", options['name'], "status set to", options['status'])
