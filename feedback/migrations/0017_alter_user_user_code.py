# Generated by Django 4.2.4 on 2023-10-17 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0016_alter_user_user_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='user_code',
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
