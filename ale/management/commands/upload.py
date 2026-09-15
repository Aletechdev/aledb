from django.core.management import BaseCommand, CommandError
from builder.ale_experiment import upload_ale_collection


class Command(BaseCommand):

    help = "This function is used to upload collection(s) of experiments."

    def add_arguments(self, parser):
        parser.add_argument('path(s)', nargs='+', type=str, help='Path(s) to you experiment directories')

    def handle(self, *args, **options):
        paths = options['path(s)']
        errors = []
        for path in paths:
            print("Uploading", path)
            experiment_count, failed_paths = upload_ale_collection(path)
            if experiment_count == 0:
                errors.append(
                    "no experiments found under %s "
                    "(expected <sample>/breseq and <sample>/metadata directories)" % path)
            for failed_path in failed_paths:
                errors.append("experiment failed: %s" % failed_path)
            print("Finished", path, "-", experiment_count - len(failed_paths), "of", experiment_count, "experiments ok")
        if errors:
            raise CommandError("\n".join(errors))
