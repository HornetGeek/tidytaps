# Generated by Django 4.1.4 on 2023-12-11 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0019_rename_numberofvist_clients_numberoforders_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clients',
            name='numberOfOrders',
            field=models.IntegerField(default=0),
        ),
    ]
