# Generated by Django 4.1.4 on 2024-01-11 18:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0025_order_pay'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='pay',
            field=models.CharField(choices=[('cash', 'cash'), ('payment', 'payment')], default='cash', max_length=50, null=True),
        ),
    ]
