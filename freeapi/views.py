from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.db.models import Count
from django.shortcuts import render
from .serializers import *
from django.contrib.auth.decorators import login_required
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
# Create your views here.
from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

class IndexView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            account = Account.objects.get(user=request.user)  # Assuming one-to-one with User
        except Account.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Serialize the account data using the AccountSerializer
        serializer = AccountSerializer(account)

        # Get the serialized data dictionary
        serialized_data = serializer.data

        return Response(serialized_data, status=status.HTTP_200_OK)

class ChartIndex(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        username = request.user.username

        account = Account.objects.get(user=request.user)
        current_date = timezone.now()
        start_date = current_date - timedelta(days=6)  # For a week

        day_names = {
            0: "Monday",
            1: "Tuesday",
            2: "Wednesday",
            3: "Thursday",
            4: "Friday",
            5: "Saturday",
            6: "Sunday"
        }
        stats = {"Monday":0, "Tuesday":0, "Wednesday": 0, "Thursday":0,"Friday":0, "Saturday":0, "Sunday":0 }
        orders_by_day = Order.objects.filter(account=account,date__gte=start_date).extra({'day': "date(date)"}).values('day').annotate(order_count=Count('id')).order_by('day')   
        print(orders_by_day) 
        for entry in orders_by_day:
            day_date_str = entry['day']  # Assuming 'day' is a string representation of the date
            print(day_date_str)
            day_date = datetime.strptime(day_date_str, '%Y-%m-%d')  # Convert string to datetime object
            print(day_date)
            day_number = day_date.weekday()  # Get the weekday number from the date
            day_name = day_names[day_number]
            stats[day_name] = entry['order_count']  # Map the number to the day name

        return JsonResponse(stats)


class LoginView(APIView):
    http_method_names = ['post']
    permission_classes = [BasePermission]
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Username or password is missing'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        token = RefreshToken.for_user(user)
        return Response({'token': str(token.access_token)}, status=status.HTTP_200_OK)

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LastClientView(APIView):
    def get(self, request):
        account = Account.objects.get(user=request.user)
        last_10_clients = Clients.objects.filter(account=account).order_by('-date')[:10]
        serializer = ClientSerializer(last_10_clients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OfferDetailView(APIView):
    permission_classes = [IsAuthenticated]  # Optional authentication

    def get(self, request, pk, format=None):
        try:
            offers = MenuItem.objects.filter(account=pk,hasOffer=True)
            serialized_offers = [MenuItemSerializer(offer).data for offer in offers]
            return Response(serialized_offers)
        except Offers.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
    def post(self, request, format=None):
        serializer = MenuItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        try:
            offer = Offers.objects.get(pk=pk)
            serializer = OfferSerializer(offer, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Offers.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk, format=None):
        try:
            offer = Offers.objects.get(pk=pk)
            offer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)  # No content to return
        except Offers.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        



class MenuItemDetailView(APIView):
    permission_classes = [IsAuthenticated]  # Optional authentication

    def get(self, request, pk, format=None):
        try:
            menu_items = MenuItem.objects.filter(account=pk)  # Filter by account
            serializer = MenuItemGetSerializer(menu_items, many=True)  # Serialize multiple items
            return Response(serializer.data)
        except MenuItem.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


    def put(self, request, pk,itemId, format=None):
        try:
            menu_item = MenuItem.objects.get(account=pk, pk=itemId)
            serializer = MenuItemSerializer(menu_item, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except MenuItem.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk, format=None):
        try:
            menu_item = MenuItem.objects.get(account=pk)
            menu_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except MenuItem.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def post(self, request, format=None):
        serializer = MenuItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
