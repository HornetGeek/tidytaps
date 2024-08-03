from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime
from django.utils.translation import gettext_lazy as _
import uuid
from django.conf import settings
# Create your models here.

#class CustomUser(AbstractUser):
#    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#    CLIENT = 'client'
#    SUB_ACCOUNT = 'sub_account'

#    ROLE_CHOICES = [
#        (CLIENT, 'Client'),
#        (SUB_ACCOUNT, 'Sub Account'),
        # Add more roles if needed
#    ]

#    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=CLIENT)
#    parent_account = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)


class Account(models.Model):
    accountId = models.UUIDField(default=uuid.uuid4, unique=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name="account_data")
    username = models.CharField(max_length=150, unique=True)
    #password = models.CharField(max_length=128)
    phone_number = models.IntegerField(blank=True, null=True)

    idnumber = models.IntegerField(blank=True, null=True)
    picture = models.CharField(max_length=200, blank=True)
    telegramId = models.CharField(max_length=150, default="", blank=True)

    
    #objects = CustomUserManager()

    def __str__(self):
        return self.username

class OneLink(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="onelink_account")
    link = models.CharField(max_length=500, default="")
    date = models.DateTimeField(default=datetime.now)

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
    orderId = models.IntegerField(default=0)
    price = models.FloatField()
    status = models.CharField(
        max_length=50,
        choices=[('Done', 'Done'), ('canceled' , 'canceled'), ('waiting','waiting')],
        default='waiting'
    )
    tableNum = models.IntegerField(default=0)
    date = models.DateTimeField()
    item = models.CharField(max_length=300,blank=True, null=True)
    quantity = models.IntegerField(default=0)
    note = models.CharField(max_length=300,blank=True, null=True)
    size = models.CharField(max_length=300,default='s')
    modifier = models.CharField(max_length=300,blank=True, null=True)
    modifier_note = models.CharField(max_length=300,blank=True, null=True)
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


class Menu(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="menu_account")
    title = models.CharField(max_length=500, default=_("Menu Title"))
    logo = models.FileField(upload_to='accounts/static/img/logos')
    def __str__(self):
        return 'Menu'

class Category(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="Category_account", null=True)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name="category_menu")
    name = models.CharField(max_length=500, unique=True)
    def __str__(self):
        return self.name

class MenuItem(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="MenuItem_account" , null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="menuitem_categgory")
    item = models.CharField(max_length=500)
    price = models.CharField(max_length=500)
    old_price = models.CharField(max_length=500, default="")
    hasOffer = models.BooleanField(default=False)
    desc = models.CharField(max_length=500, blank=True)
    picture = models.FileField(upload_to='static/img/items/')

    def __str__(self):
        return self.item

class Modifier(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="Modifier_account",  null=True)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="menuitem_Modifier")
    name = models.CharField(max_length=500)
    price = models.CharField(max_length=500, default=0)
    pic = models.FileField(upload_to='static/img/modifier/',blank=True )

class SizeModifier(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="SizeModifier_account",  null=True)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="menuitem_SizeModifier")
    size = models.CharField(max_length=500)
    price = models.CharField(max_length=500, default=0)

    def __str__(self):
        return self.menuitem.item

class Offers(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    message = models.CharField(max_length=500, default="")
    photo = models.FileField(upload_to='static/img/offers/',blank=True )

class Options(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="menuitem_Options")
    name = models.CharField(max_length=500)
    Popular = models.BooleanField(default=False)

