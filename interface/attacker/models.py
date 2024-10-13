from django.db import models
import uuid
from django.utils import timezone


class Campaign(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    template_id = models.UUIDField(default=uuid.uuid4)
    template_type = models.CharField(max_length=10, choices=[('default', 'Default'), ('custom', 'Custom')], null=True, blank=True)
    attachment = models.FileField(upload_to='campaign_attachments/', null=True, blank=True)
    attachment_link = models.URLField(null=True, blank=True)
    original_attachment_link = models.URLField(null=True, blank=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=20, choices=[
        ('seconds', 'Seconds'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], null=True, blank=True)
    recurrence_interval = models.IntegerField(default=1)  # New field for interval
    last_run = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    recurrence_count = models.IntegerField(default=0)  # 0 means infinite
    recurrence_sent = models.IntegerField(default=0)  # Track how many times it has been sent

    def __str__(self):
        return self.name

    def is_due(self):
        if not self.scheduled_time:
            return False
        if self.recurrence_count > 0 and self.recurrence_sent >= self.recurrence_count:
            return False
        return timezone.now() >= self.scheduled_time

    def get_email_data(self):
        return {
            'campaign_name': self.name,
            'template_id': str(self.template_id),
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'is_recurring': self.is_recurring,
            'recurrence_pattern': self.recurrence_pattern,
            'recurrence_interval': self.recurrence_interval,
            'recurrence_count': self.recurrence_count,
            # Add all other necessary fields
        }



class EmailTrackingLog(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='tracking_logs')
    tracking_id = models.UUIDField()
    link_id = models.CharField(max_length=50, null=True, blank=True)
    recipient = models.EmailField()
    action = models.CharField(max_length=20)
    s_ipv4_address = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True)
    s_ipv6_address = models.GenericIPAddressField(protocol='IPv6', null=True, blank=True)
    c_ipv4_address = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True)
    c_ipv6_address = models.GenericIPAddressField(protocol='IPv6', null=True, blank=True)
    ip_data = models.JSONField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    device_info = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient} - {self.action} - {self.timestamp}"



class Template(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    html_content = models.TextField()
    thumbnail = models.ImageField(upload_to='template_thumbnails/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CustomTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    html_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class LinkTracking(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='link_trackings')
    original_link = models.URLField()
    tracking_link = models.URLField(unique=True)
    link_id = models.CharField(max_length=50)
    tracking_id = models.UUIDField()
    clicks = models.IntegerField(default=0)
    last_clicked = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.original_link} -> {self.tracking_link}"


