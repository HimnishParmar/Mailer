from django.core.management.base import BaseCommand
from django.utils import timezone
from attacker.models import Campaign
from attacker.views import send_email
from django.test import RequestFactory
import json

class Command(BaseCommand):
    help = 'Run scheduled campaigns'

    def handle(self, *args, **options):
        now = timezone.now()
        campaigns = Campaign.objects.filter(scheduled_time__lte=now, is_active=True)

        for campaign in campaigns:
            self.stdout.write(f"Running campaign: {campaign.name}")
            
            # Create a fake request to pass to send_email
            factory = RequestFactory()
            request = factory.post('/send-email/', json.dumps(campaign.get_email_data()), content_type='application/json')
            
            response = send_email(request)
            
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS(f"Successfully sent campaign: {campaign.name}"))
                
                campaign.recurrence_sent += 1
                
                if campaign.is_recurring:
                    # Update the scheduled time for the next run
                    if campaign.recurrence_pattern == 'seconds':
                        campaign.scheduled_time += timezone.timedelta(seconds=campaign.recurrence_interval)
                    elif campaign.recurrence_pattern == 'daily':
                        campaign.scheduled_time += timezone.timedelta(days=campaign.recurrence_interval)
                    elif campaign.recurrence_pattern == 'weekly':
                        campaign.scheduled_time += timezone.timedelta(weeks=campaign.recurrence_interval)
                    elif campaign.recurrence_pattern == 'monthly':
                        campaign.scheduled_time += timezone.timedelta(days=30 * campaign.recurrence_interval)  # Approximate
                    
                    if campaign.recurrence_count > 0 and campaign.recurrence_sent >= campaign.recurrence_count:
                        campaign.is_active = False
                    
                    campaign.save()
                else:
                    campaign.is_active = False
                    campaign.save()
            else:
                self.stdout.write(self.style.ERROR(f"Failed to send campaign: {campaign.name}"))

        self.stdout.write(self.style.SUCCESS('Finished running scheduled campaigns'))