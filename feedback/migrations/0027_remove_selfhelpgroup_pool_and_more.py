# Generated by Django 4.2.4 on 2025-04-13 05:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0026_shgloan_total_payable_alter_shgloan_principal_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='selfhelpgroup',
            name='pool',
        ),
        migrations.RemoveField(
            model_name='shgcontribution',
            name='amount',
        ),
        migrations.AddField(
            model_name='shgcontribution',
            name='contrib',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
