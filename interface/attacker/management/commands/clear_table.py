from django.core.management.base import BaseCommand
from attacker.models import LinkTracking, EmailTrackingLog, Campaign

class Command(BaseCommand):
    help = 'Truncate a table'

    def handle(self, *args, **kwargs):
        LinkTracking.objects.all().delete()
        EmailTrackingLog.objects.all().delete()
        Campaign.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Table has been truncated.'))
