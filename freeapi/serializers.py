from rest_framework import serializers
from accounts.models import *
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JwtTokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.db import IntegrityError


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'], validated_data['password'])
        return user

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.save()

        user = instance.user
        user.set_password(validated_data['password'])
        user.save()
        return instance

    class Meta:
        model = User
        fields = ('username', 'password')

class AccountPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('__all__')  # Replace with specific fields you want to expose

    def create(self, validated_data):
        while True:
            try:
                account = Account(**validated_data)
                account.save()
                return account
            except IntegrityError:
                print("inside Integrity Error of AccountId")
                # Regenerate accountId if there is a conflict
                validated_data['accountId'] = str(uuid.uuid4())

class AccountSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)  # Assuming one-to-one with User
    orders_count = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    payment_amount = serializers.SerializerMethodField()
    offers_count = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ('username', 'orders_count', 'reviews_count', 'payment_amount', 'offers_count')

    def get_orders_count(self, obj):
        return Order.objects.filter(account=obj).count()

    def get_reviews_count(self, obj):
        return Reviews.objects.filter(account=obj).count()

    def get_payment_amount(self, obj):
        payments = Payment.objects.filter(account=obj)
        return payments.aggregate(total_amount=Sum('amount'))['total_amount'] or 0

    def get_offers_count(self, obj):
        return Offers.objects.filter(account=obj).count()

class ContactsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contacts
        fields = '__all__'

class AdressesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Adresses
        fields = '__all__'
        
class CoverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cover
        fields = ['id', 'account', 'cover']  # Include all fields you want to expose in the API
        extra_kwargs = {
            'account': {'write_only': True}  # Make 'account' writable only, so you can create/update by account_id
        }
class SocialMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMedia
        fields = '__all__'

class DeliverySerializer(serializers.ModelSerializer):
    account = AccountSerializer()  # Include the AccountSerializer to embed account details

    class Meta:
        model = Delivery
        fields = ['account', 'amount', "city"]

class DeliveryPostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Delivery
        fields = ['account', 'amount', "city"]


class MenuItemPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItemPhoto
        fields = ['id', 'account', 'menuitem', 'picture']
        
          
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('__all__')  # Replace with specific fields you want to expose



class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clients
        fields = ('__all__')  # Replace with specific fields you want to expose

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('__all__')  # Replace with specific fields you want to expose

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reviews
        fields = ('__all__')  # Replace with specific fields you want to expose

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('__all__')  # Replace with specific fields you want to expose

class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offers
        fields = ('__all__')  # Replace with specific fields you want to expose


class MenuItemGetSerializer(serializers.ModelSerializer):
    account = AccountSerializer(read_only=True)  # Nested serializer for account data

    class Meta:
        model = MenuItem
        fields = ('__all__')

class MenuItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = MenuItem
        fields = ('__all__')


class CategoryWithItemsSerializer(serializers.ModelSerializer):
    menuitem_categgory = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'picture', 'menuitem_categgory')

    def get_menuitem_categgory(self, obj):
        account_id = self.context['request'].parser_context['kwargs']['account_id']
        return MenuItemSerializer(obj.menuitem_categgory.filter(account__id=account_id), many=True).data

class OptionsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Option
        fields = ('__all__')


class MenuItemChoicesSerializer(serializers.ModelSerializer):

    class Meta:
        model = MenuItemChoices
        fields = ('__all__')



class ShopOrderItemSerializer(serializers.ModelSerializer):
    choices = serializers.PrimaryKeyRelatedField(many=True, queryset=MenuItemChoices.objects.all())
    
    class Meta:
        model = ShopOrderItem
        fields = ['item', 'quantity', 'choices']

class ShopOrderGetItemSerializer(serializers.ModelSerializer):
    item = MenuItemSerializer()
    choices = MenuItemChoicesSerializer(many=True)
    
    class Meta:
        model = ShopOrderItem
        fields = ['item', 'quantity', 'choices']


class ShopOrderSerializer(serializers.ModelSerializer):
    items = ShopOrderItemSerializer(many=True)
    phone = serializers.CharField(write_only=True)  # Accept phone only for input
    username = serializers.CharField(write_only=True, required=False)  # Accept username only for input

    class Meta:
        model = ShopOrder
        fields = [
            'id',
            'account', 'subtotal', 'shipping', 'total_amount',
            'service_type', 'address_street', 'address_apartment',
            'address_city', 'order_status', 'items', 'phone', 'username'
        ]

    def create(self, validated_data):
        # Extract phone and username from validated data
        phone = validated_data.pop('phone', None)
        username = validated_data.pop('username', None)
        items_data = validated_data.pop('items')
        account = validated_data['account']

        # Find or create the client
        client, created = Clients.objects.get_or_create(
            phone=phone,
            account=account,
            defaults={'username': username or ""}
        )
        if not created and username:  # Update username if it was empty before
            client.username = username
            client.save()

        # Add the client to the ShopOrder data
        validated_data['client'] = client

        # Create the ShopOrder instance
        order = ShopOrder.objects.create(**validated_data)

        # Create ShopOrderItem instances
        for item_data in items_data:
            choices = item_data.pop('choices', [])
            order_item = ShopOrderItem.objects.create(order=order, **item_data)
            order_item.choices.set(choices)

        return order



class ShopOrderGetSerializer(serializers.ModelSerializer):
    items = ShopOrderGetItemSerializer(many=True)
    phone = serializers.CharField(write_only=True)  # Accept phone only for input
    client = ClientSerializer(read_only=True)
    username = serializers.CharField(write_only=True, required=False)  # Accept username only for input

    class Meta:
        model = ShopOrder
        fields = [
            'id','client',
            'account', 'subtotal', 'shipping', 'total_amount',
            'service_type', 'address_street', 'address_apartment',
            'address_city', 'order_status', 'items', 'phone', 'username'
        ]

    def create(self, validated_data):
        # Extract phone and username from validated data
        phone = validated_data.pop('phone', None)
        username = validated_data.pop('username', None)
        items_data = validated_data.pop('items')
        account = validated_data['account']

        # Find or create the client
        client, created = Clients.objects.get_or_create(
            phone=phone,
            account=account,
            defaults={'username': username or ""}
        )
        if not created and username:  # Update username if it was empty before
            client.username = username
            client.save()

        # Add the client to the ShopOrder data
        validated_data['client'] = client

        # Create the ShopOrder instance
        order = ShopOrder.objects.create(**validated_data)

        # Create ShopOrderItem instances
        for item_data in items_data:
            choices = item_data.pop('choices', [])
            order_item = ShopOrderItem.objects.create(order=order, **item_data)
            order_item.choices.set(choices)

        return order


class ShopCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ShopCategory
        fields = ('__all__')

