# Generated by Django 5.1.1 on 2024-10-13 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attacker', '0009_rename_ip_address_emailtrackinglog_ipv4_address_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emailtrackinglog',
            name='ipv4_address',
        ),
        migrations.RemoveField(
            model_name='emailtrackinglog',
            name='ipv6_address',
        ),
        migrations.AddField(
            model_name='emailtrackinglog',
            name='c_ipv4_address',
            field=models.GenericIPAddressField(blank=True, null=True, protocol='IPv4'),
        ),
        migrations.AddField(
            model_name='emailtrackinglog',
            name='c_ipv6_address',
            field=models.GenericIPAddressField(blank=True, null=True, protocol='IPv6'),
        ),
        migrations.AddField(
            model_name='emailtrackinglog',
            name='s_ipv4_address',
            field=models.GenericIPAddressField(blank=True, null=True, protocol='IPv4'),
        ),
        migrations.AddField(
            model_name='emailtrackinglog',
            name='s_ipv6_address',
            field=models.GenericIPAddressField(blank=True, null=True, protocol='IPv6'),
        ),
    ]