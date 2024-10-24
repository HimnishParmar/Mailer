# Generated by Django 5.1.1 on 2024-10-02 21:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attacker', '0004_campaign_attachment_link_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='LinkTracking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_link', models.URLField()),
                ('tracking_link', models.URLField(unique=True)),
                ('link_id', models.CharField(max_length=50)),
                ('tracking_id', models.UUIDField()),
                ('clicks', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='link_trackings', to='attacker.campaign')),
            ],
        ),
    ]
