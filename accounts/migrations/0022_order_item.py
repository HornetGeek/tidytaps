# Generated by Django 4.1.4 on 2023-12-21 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_notifications'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='item',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]
