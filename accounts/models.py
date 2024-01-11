from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
# Create your models here.

class Account(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    phone_number = models.IntegerField(blank=True, null=True)
    
    idnumber = models.IntegerField(blank=True, null=True)
    picture = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.user.username

class Clients(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="clients_data")
    username = models.CharField(max_length=500, default="")
    email = models.CharField(max_length=500,default="")
    phone = models.CharField(max_length=500,default=0)
    numberOfOrders = models.IntegerField(default=0)
    date = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return self.username

class Notifications(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="acount_notifications")
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name="client_notifications")
    message = models.CharField(max_length=500,default="")
    read = models.CharField(
        max_length=50,
        choices=[('yes', 'yes'), ('no' , 'no')],
        default='no'
    )

class Reviews(models.Model):
    reviewer = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name="reviewer")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="reviewee")
    reviewe_text = models.CharField(max_length=500)
    stars = models.IntegerField(default=0)

class Payment(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="acount_payments")
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name="client_payments")
    amount = models.IntegerField(default=0)
    time = models.DateTimeField()

class Order(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name="client_order")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="freelancer_order")
    price = models.IntegerField()
    status = models.CharField(
        max_length=50,
        choices=[('Done', 'Done'), ('canceled' , 'canceled'), ('waiting','waiting')],
        default='waiting'
    )
    
    date = models.DateTimeField()
    item = models.CharField(max_length=300,blank=True, null=True)
    quantity = models.IntegerField(default=0)
    note = models.CharField(max_length=300,blank=True, null=True)

    pay = models.CharField(
        max_length=50,
        choices=[('cash', 'cash'), ('payment' , 'payment')],
        default='cash',
        null=True
    )
    

    def __str__(self):
        return self.status
    
    def client_name(self):
        return self.client.user.username

class Offers(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name="client_offers")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="account_offers")
    message = models.CharField(max_length=500)