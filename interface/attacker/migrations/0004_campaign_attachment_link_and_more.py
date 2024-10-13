# Generated by Django 5.1.1 on 2024-10-02 20:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attacker', '0003_campaign_attachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='attachment_link',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='campaign',
            name='original_attachment_link',
            field=models.URLField(blank=True, null=True),
        ),
    ]
