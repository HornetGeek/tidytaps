# Generated by Django 4.1.4 on 2023-12-12 00:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0020_alter_clients_numberoforders'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notifications',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(default='', max_length=500)),
                ('read', models.CharField(choices=[('yes', 'yes'), ('no', 'no')], default='no', max_length=50)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='acount_notifications', to='accounts.account')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='client_notifications', to='accounts.clients')),
            ],
        ),
    ]
