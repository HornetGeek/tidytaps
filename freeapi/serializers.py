from rest_framework import serializers
from accounts.models import *
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JwtTokenObtainPairSerializer
from django.contrib.auth import get_user_model



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
