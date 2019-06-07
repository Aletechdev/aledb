
from django.core.management import BaseCommand
from dashboard.util import rebuild_dashboard_data


class Command(BaseCommand):
    def handle(self, *args, **options):
        rebuild_dashboard_data()
