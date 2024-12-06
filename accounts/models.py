from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime
from django.utils.translation import gettext_lazy as _
import uuid
from django.conf import settings
from django.utils.timezone import now

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
    CURRENCY_CHOICES = [
        ("EGP", "Egyptian Pound"),
        ("SAR", "Saudi Riyal"),
        ("AED", "UAE Dirham"),
        ("SYP", "Syrian Pound"),
        ("KWD", "Kuwaiti Dinar"),
        ("QAR", "Qatari Riyal"),
        ("BHD", "Bahraini Dinar"),
        ("LYD", "Libyan Dinar"),
        ("OMR", "Omani Rial"),
        ("JOD", "Jordanian Dinar"),  
        ("MAD", "Moroccan Dirham"),
        ("TND", "Tunisian Dinar"),
        ("LBP", "Lebanese Pound"),
        ("SDG", "Sudanese Pound"),
        ("DZD", "Algerian Dinar"),
        ("YER", "Yemeni Rial"),
        ("IQD", "Iraqi Dinar"),
        ("USD", "US Dollar"),
        ("EUR", "Euro"),
        ("GBP", "British Pound"),
        ("JPY", "Japanese Yen"),
        ("AUD", "Australian Dollar"),
        ("CAD", "Canadian Dollar"),
        ("CHF", "Swiss Franc"),
        ("CNY", "Chinese Yuan"),
        ("SEK", "Swedish Krona"),
        ("NZD", "New Zealand Dollar"),
    ]
    SUBSCRIPTION_CHOICES = [
        ("free", "Free"),
        ("basic", "Basic"),
        ("premium", "Premium"),
    ]
    THEME_CHOICES = [
        ("f", "f"),
        ("p", "p"),
    ]

    accountId = models.CharField(max_length=255, default=str(uuid.uuid4))
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name="account_data")
    username = models.CharField(max_length=150, unique=True)
    #password = models.CharField(max_length=128)
    phone_number = models.IntegerField(blank=True, null=True)

    idnumber = models.IntegerField(blank=True, null=True)
    picture = models.CharField(max_length=200, blank=True)
    telegramId = models.CharField(max_length=150, default="", blank=True)
    logo = models.FileField(upload_to='static/img/logos', default="static/img/logos/Defaultlogo.png")
    title = models.CharField(max_length=150, default="", blank=True)
    primary_color = models.CharField(max_length=7, default="#0E214B", blank=True)
    second_color = models.CharField(max_length=7, default="#3F68DE",blank=True)
    language = models.CharField(max_length=10, default='en', null=True, blank=True)
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default="EGP", blank=True
    )
    subscription_plan = models.CharField(
        max_length=10, choices=SUBSCRIPTION_CHOICES, default="free"
    )  # New field for subscription plan
    selected_theme = models.CharField(max_length=10, choices=THEME_CHOICES, default="light")  # New field for theme selection
    #objects = CustomUserManager()

    def __str__(self):
        return self.username

class CouponCode(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="coupon_account")
    code = models.CharField(max_length=500,default="")
    amount = models.CharField(max_length=500,default="")

    
class Cover(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="cover_account")
    cover = models.FileField(upload_to='static/img/covers')
    
class Delivery(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="delivery_account")
    city = models.CharField(max_length=500,default="")
    amount = models.CharField(max_length=500,default=0)

class Contacts(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="conatcts_account")
    phone = models.IntegerField(default=0)
    emails = models.CharField(max_length=150, default="")

class Adresses(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="adress_account")
    address = models.CharField(max_length=150, default="")

class SocialMedia(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="socialMedia_account")
    facebook = models.CharField(max_length=150, default="")
    whatsapp = models.CharField(max_length=150, default="")
    youtube = models.CharField(max_length=150, default="")
    instagram = models.CharField(max_length=150, default="")
    tiktok = models.CharField(max_length=150, default="")

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
    name = models.CharField(max_length=500)
    picture = models.FileField(upload_to='static/img/category', default="")
    class Meta:
        unique_together = ('account', 'name')  # Enforce uniqueness per account

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

class MenuItemPhoto(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="menuitem_photos")
    picture = models.FileField(upload_to='static/img/items/')

    
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


class ShopMenu(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    title = models.CharField(max_length=500, default=_("Menu Title"))
    logo = models.FileField(upload_to='accounts/static/img/logos')
    def __str__(self):
        return 'Menu'

class ShopCategory(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE , null=True)
    name = models.CharField(max_length=500, unique=True)
    def __str__(self):
        return self.name


class Offers(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    message = models.CharField(max_length=500, default="")
    photo = models.FileField(upload_to='static/img/offers/',blank=True )

class Option(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    Item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=[('text', 'Text'), ('number', 'Number'), ('date', 'Date'), ('checkbox', 'Checkbox')])
    required = models.BooleanField(default=False)

class MenuItemChoices(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="menuitem_Options")
    option = models.ForeignKey(Option, on_delete=models.CASCADE,default=1)
    name = models.CharField(max_length=500)
    price = models.CharField(max_length=500, default=0)
    Popular = models.BooleanField(default=False)

class ShopOrder(models.Model):
    account = models.ForeignKey('Account', on_delete=models.CASCADE)
    client = models.ForeignKey('Clients', on_delete=models.CASCADE)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Store the subtotal
    shipping = models.CharField(max_length=50, default="Free")  # Store shipping details
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Total including shipping
    service_type = models.CharField(max_length=20, choices=[('self-pickup', 'Self-Pickup'), ('delivery', 'Delivery')], default='self-pickup')
    address_street = models.CharField(max_length=255, blank=True, null=True)  # Optional, for delivery only
    address_apartment = models.CharField(max_length=255, blank=True, null=True)
    address_city = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateTimeField(default=now)
    order_status = models.CharField(max_length=30, default='pending')
    
    def __str__(self):
        return f"Order #{self.id} - {self.client} - {self.order_status}"

class ShopOrderItem(models.Model):
    order = models.ForeignKey(ShopOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey('MenuItem', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    choices = models.ManyToManyField('MenuItemChoices', blank=True)

    def __str__(self):
        return f"{self.item} x {self.quantity} for Order #{self.order.id}"