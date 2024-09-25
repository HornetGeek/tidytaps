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
from rest_framework import viewsets


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

        user = authenticate(username=username, password=str(password))
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        token = RefreshToken.for_user(user)
        return Response({'token': str(token.access_token)}, status=status.HTTP_200_OK)

class RegisterView(APIView):
    permission_classes = [BasePermission]
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


class MenuItemOptionsViewSet(viewsets.ModelViewSet):
    queryset = MenuItemChoices.objects.all()
    serializer_class = MenuItemChoicesSerializer

def get_items_by_account_and_menuitem(request, account_id, menuitem_id, option_id):
    items = MenuItemChoices.objects.filter(account=account_id, menuitem=menuitem_id, option=option_id)
    serializer = MenuItemChoicesSerializer(items, many=True)  
    return JsonResponse(serializer.data, safe=False)

class MenuOptionsViewSet(viewsets.ModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionsSerializer

def get_option_by_account_and_menuitem(request, account_id, menuitem_id):
    items = Option.objects.filter(account=account_id, Item=menuitem_id)
    serializer = OptionsSerializer(items, many=True)  
    return JsonResponse(serializer.data, safe=False)


class MakeOrderView(APIView):
    def get(self, request, format=None):
        orders = ShopOrder.objects.all()
        serializer = ShopOrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        if not isinstance(request.data, list):
            return Response({'error': 'Invalid data format. Please provide a list of orders.'}, status=status.HTTP_400_BAD_REQUEST)

        account = Account.objects.get(user=request.data[0]["account"])

        # Check for existing client based on phone number (consider username too)
        client, created = Clients.objects.get_or_create(
            account=account,
            phone=request.data[0]["phone"],
            defaults={'numberOfOrders': 0, 'email': request.data[0]["email"]},  # Set defaults for new clients
        )
        if created:
            client.numberOfOrders = 0  # Initialize numberOfOrders if creating a new client

        orders = []
        for order_data in request.data:
            serializer = ShopOrderSerializer(data=order_data)

            # Validate order data before saving
            #if not serializer.is_valid():
            #    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve or create ShopOrder object
            print("client")
            print(client)
            order, created = ShopOrder.objects.get_or_create(
                account=account,
                client=client.id,
                Item_id=order_data["Item"],  # Use foreign key field name (e.g., Item_id)
                quantity=order_data["quantity"],
                date=order_data.get("date", datetime.now()),  # Use default for missing date
            )

            # Handle options based on your model design:
            if "options" in order_data:
                # Option 1: Directly associate options with `ShopOrder` using a ManyToManyField
                # (Update `Option` model with a `ShopOrder` relationship if needed)
                for option_data in order_data["options"]:
                    order.options.add(Option.objects.get(pk=option_data["optionId"]))

                # Option 2: Save additional information about chosen options
                # (Update `ShopOrder` model if needed to store chosen option details)
                order.chosen_options = order_data["options"]  # Replace with actual field name

            # Save the order
            order.save()
            orders.append(order)

        # Update client's number of orders if necessary
        client.numberOfOrders += len(orders)
        client.save()

    def put(self, request, pk, format=None):  

        order = ShopOrder.objects.get(pk=pk)
        serializer = ShopOrderSerializer(order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):  

        order = ShopOrder.objects.get(pk=pk)
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)