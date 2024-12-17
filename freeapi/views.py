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
from rest_framework import viewsets, filters
from rest_framework import generics
from rest_framework.generics import RetrieveAPIView
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.decorators import action

class ReadOnlyUserPermission(permissions.BasePermission):
    """
    Custom permission to restrict "Read-Only Users" from performing create, update, or delete operations.
    """
    def has_permission(self, request, view):
        # Allow safe methods for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Restrict unsafe methods for users in the "Read-Only Users" group
        is_read_only_user = request.user.groups.filter(name="Read-Only Users").exists()
        if is_read_only_user and request.method not in permissions.SAFE_METHODS:
            return False
        
        # Allow other authenticated users to proceed
        return request.user.is_authenticated

class IsHornetUser(permissions.BasePermission):
    """
    Custom permission to allow access only to the user with username 'hornet'.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated and their username is "hornet"
        return request.user.is_authenticated and request.user.username == "hornet"

class AccountCreateAPIView(generics.ListCreateAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountPostSerializer

    permission_classes = [IsHornetUser]


class AccountRetrieveByUsernameAPIView(generics.RetrieveAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountPostSerializer
    lookup_field = 'username'  # Specify that the lookup field is 'username'

    permission_classes = [ReadOnlyUserPermission]

class AccountUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountPostSerializer
    lookup_field = 'id'  # This tells Django to look for 'id' in the URL

    permission_classes = [ReadOnlyUserPermission]

class ContactsListCreateAPIView(generics.ListCreateAPIView):
    queryset = Contacts.objects.all()
    serializer_class = ContactsSerializer
    
    permission_classes = [ReadOnlyUserPermission]

    def get_queryset(self):
        account_id = self.kwargs.get('account_id')  # Get the account_id from the URL
        return Contacts.objects.filter(account__id=account_id)  # Filter contacts by account_id
    

class ContactsRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Contacts.objects.all()
    serializer_class = ContactsSerializer
    permission_classes = [ReadOnlyUserPermission]
# CRUD for Adresses
class AdressesListCreateAPIView(generics.ListCreateAPIView):
    queryset = Adresses.objects.all()
    serializer_class = AdressesSerializer
    
    permission_classes = [ReadOnlyUserPermission]
    def get_queryset(self):
        account_id = self.kwargs.get('account_id')
        return Adresses.objects.filter(account__id=account_id)  # Filter addresses by account_id


class AdressesRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Adresses.objects.all()
    serializer_class = AdressesSerializer
    
    permission_classes = [ReadOnlyUserPermission]
# CRUD for SocialMedia

class SocialMediaListCreateAPIView(generics.ListCreateAPIView):
    queryset = SocialMedia.objects.all()
    serializer_class = SocialMediaSerializer
    
    permission_classes = [ReadOnlyUserPermission]
    def get_queryset(self):
        account_id = self.kwargs.get('account_id')
        return SocialMedia.objects.filter(account__id=account_id)  # Filter social media by account_id


class DeliveryByAccountIdView(APIView):
    permission_classes = [ReadOnlyUserPermission]
    def get(self, request, account_id):
        try:
            account = Account.objects.get(id=account_id)
            
            # Fetch all deliveries related to this account
            deliveries = Delivery.objects.filter(account=account)

            # Check if deliveries exist for the account
            if not deliveries:
                return Response({'error': 'No deliveries found for this account'}, status=404)

            # Serialize the deliveries data
            serializer = DeliverySerializer(deliveries, many=True)
            return Response(serializer.data)
        
        except Account.DoesNotExist:
            return Response({'error': 'Account not found'}, status=404)
        
    def post(self, request):
        try:
            serializer = DeliveryPostSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()  # Associate the created delivery with the account
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors,)
        except Exception as e :
            print(str(e))
    # Get Delivery by Username
class DeliveryByUsernameView(APIView):
    permission_classes = [ReadOnlyUserPermission]

    def get(self, request, username):
        try:
            account = Account.objects.get(username=username)

            deliveries = Delivery.objects.filter(account=account)

            # Check if deliveries exist for the account
            if not deliveries:
                return Response({'error': 'No deliveries found for this account'}, status=404)

            # Serialize the deliveries data
            serializer = DeliverySerializer(deliveries, many=True)
            return Response(serializer.data)
        
        except Account.DoesNotExist:
            return Response({'error': 'Account not found'}, status=404)


class MenuItemPhotoViewSet(viewsets.ModelViewSet):
    queryset = MenuItemPhoto.objects.all()
    serializer_class = MenuItemPhotoSerializer

    permission_classes = [ReadOnlyUserPermission]

    def perform_create(self, serializer):
        # You can customize any behavior here, for example linking the photo with a specific account
        serializer.save()

class MenuItemPhotoListByAccountAndMenuItemView(generics.ListAPIView):
    permission_classes = [BasePermission]
    serializer_class = MenuItemPhotoSerializer
    
    permission_classes = [ReadOnlyUserPermission]

    def get_queryset(self):
        account_id = self.kwargs['account_id']  # Fetch account_id from URL params
        menuitem_id = self.kwargs['menuitem_id']  # Fetch menuitem_id from URL params
        return MenuItemPhoto.objects.filter(account_id=account_id, menuitem_id=menuitem_id)


class SocialMediaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SocialMedia.objects.all()
    serializer_class = SocialMediaSerializer
    permission_classes = [ReadOnlyUserPermission]

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


class CoverViewSet(viewsets.ModelViewSet):
    queryset = Cover.objects.all()
    serializer_class = CoverSerializer
    permission_classes = [ReadOnlyUserPermission]

    def get_queryset(self):
        account_id = self.request.query_params.get('account_id')
        if account_id:
            return self.queryset.filter(account__id=account_id)
        return self.queryset

    def create(self, request, *args, **kwargs):
        account_id = request.data.get('account')
        if not account_id:
            return Response({"detail": "Account ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)
    
class CategoryAPIView(generics.CreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [ReadOnlyUserPermission]


class CategoryGetAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [ReadOnlyUserPermission]

    def get_queryset(self):
        account_id = self.kwargs.get('account_id')  # Get account_id from the URL
        if account_id:
            return Category.objects.filter(account__id=account_id)  # Filter by account_id
        return Category.objects.all()  # Return all if account_id is not provided


class CategoryWithItemsAPIView(generics.ListAPIView):
    serializer_class = CategoryWithItemsSerializer
    permission_classes = [ReadOnlyUserPermission]
    def get_queryset(self):
        account_id = self.kwargs.get('account_id')  # Get account_id from the URL
        if account_id:
            return Category.objects.filter(account__id=account_id).prefetch_related('menuitem_categgory')  # Use the correct related name
        return Category.objects.none()
    
class CategoryUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [ReadOnlyUserPermission]

    def get_queryset(self):
        """
        Optionally restricts the queryset by filtering against `id`.
        """
        return Category.objects.all()
    
class LastClientView(APIView):
    permission_classes = [ReadOnlyUserPermission]
    def get(self, request):
        account = Account.objects.get(user=request.user)
        last_10_clients = Clients.objects.filter(account=account).order_by('-date')[:10]
        serializer = ClientSerializer(last_10_clients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClientsPagination(PageNumberPagination):
    page_size = 10  # Default items per page
    page_size_query_param = 'page_size'  # Allow clients to specify page size
    max_page_size = 100  # Max limit for items per page


class AllClientsByAccountView(APIView):
    permission_classes = [ReadOnlyUserPermission]

    def get(self, request, account_id):
        try:
            # Fetch the account by ID
            account = Account.objects.get(id=account_id)

            # Ensure the requesting user has permission to access this account's data

            #if account.user != request.user:
            #    return Response(
            #        {"detail": "You do not have permission to view these clients."},
            #        status=status.HTTP_403_FORBIDDEN
            #    )

            # Apply search filter if provided
            search_query = request.GET.get('search', None)

            # Fetch all clients for the given account, apply search if provided
            clients = Clients.objects.filter(account=account)
            if search_query:
                clients = clients.filter(client_name__icontains=search_query)  # Example: searching by client_name

            # Apply pagination
            paginator = ClientsPagination()
            paginated_clients = paginator.paginate_queryset(clients, request)
            serializer = ClientSerializer(paginated_clients, many=True)

            # Return paginated response
            return paginator.get_paginated_response(serializer.data)

        except Account.DoesNotExist:
            return Response(
                {"detail": "Account not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
class OfferDetailView(APIView):
    permission_classes = [ReadOnlyUserPermission]

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
    permission_classes = [ReadOnlyUserPermission]

    def get(self, request, pk, format=None):
        try:
            menu_items = MenuItem.objects.filter(account=pk)  # Filter by account
            serializer = MenuItemGetSerializer(menu_items, many=True)  # Serialize multiple items
            return Response(serializer.data)
        except MenuItem.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk, itemId, format=None):
        try:
            menu_item = MenuItem.objects.get(account=pk, pk=itemId)
            category_id = request.data.get('category')

            # Validate that the category belongs to the account
            if not Category.objects.filter(id=category_id, account=pk).exists():
                return Response({"error": "The category does not belong to this account."},
                                status=status.HTTP_400_BAD_REQUEST)

            serializer = MenuItemSerializer(menu_item, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except MenuItem.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
    def patch(self, request, pk, itemId, format=None):
        try:
            menu_item = MenuItem.objects.get(account=pk, pk=itemId)
            serializer = MenuItemSerializer(menu_item, data=request.data, partial=True)  # Partial update
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except MenuItem.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
    def delete(self, request, pk, itemId, format=None):
        try:
            menu_item = MenuItem.objects.get(account=pk, id=itemId)
            category_id = menu_item.category.id

            # Validate that the category belongs to the account
            if not Category.objects.filter(id=category_id, account=pk).exists():
                return Response({"error": "The category does not belong to this account."},
                                status=status.HTTP_400_BAD_REQUEST)

            menu_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except MenuItem.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def post(self, request, format=None):
        # Extract account_id (pk) from the request body
        account_id = request.data.get('account')
        category_id = request.data.get('category')

        # Validate that the account_id and category_id exist
        if not account_id or not Category.objects.filter(id=category_id, account=account_id).exists():
            return Response({"error": "The category does not belong to this account."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = MenuItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CouponCodeViewSet(viewsets.ModelViewSet):
    queryset = CouponCode.objects.all()
    serializer_class = CouponCodeSerializer
    permission_classes = [ReadOnlyUserPermission]

    @action(detail=False, methods=['get'], url_path='by-account/(?P<account_id>\d+)')
    def get_by_account(self, request, account_id=None):
        coupons = CouponCode.objects.filter(account_id=account_id)
        serializer = self.get_serializer(coupons, many=True)
        return Response(serializer.data)

class ValidateCouponView(APIView):
    permission_classes = [BasePermission]

    def post(self, request):
        account_id = request.data.get('account_id')
        coupon_code = request.data.get('coupon')
        total_cart = request.data.get('total_cart')  # Get the cart total from the request

        # Validate required fields
        if not account_id or not coupon_code or total_cart is None:
            return Response(
                {"error": "account_id, coupon code, and total_cart are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Retrieve the first matching coupon
            coupon = CouponCode.objects.filter(account_id=account_id, code=coupon_code).first()

            if not coupon:
                return Response(
                    {"error": "Coupon not found or invalid."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if the coupon has expired
            if coupon.expire_date and coupon.expire_date < timezone.now():
                return Response(
                    {"error": "This coupon has expired."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if total_cart meets the amount_condition
            if coupon.amount_condition and float(total_cart) < float(coupon.amount_condition):
                return Response(
                    {
                        "error": f"Cart total must be at least {coupon.amount_condition} to use this coupon."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # If all conditions are satisfied, return the discount amount
            return Response(
                {"amount": coupon.amount},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class MenuItemOptionsViewSet(viewsets.ModelViewSet):
    queryset = MenuItemChoices.objects.all()
    serializer_class = MenuItemChoicesSerializer
    permission_classes = [ReadOnlyUserPermission]

def get_items_by_account_and_menuitem(request, account_id, menuitem_id, option_id):
    items = MenuItemChoices.objects.filter(account=account_id, menuitem=menuitem_id, option=option_id)
    serializer = MenuItemChoicesSerializer(items, many=True)  
    return JsonResponse(serializer.data, safe=False)

class MenuOptionsViewSet(viewsets.ModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionsSerializer
    permission_classes = [ReadOnlyUserPermission]

def get_option_by_account_and_menuitem(request, account_id, menuitem_id):
    items = Option.objects.filter(account=account_id, Item=menuitem_id)
    serializer = OptionsSerializer(items, many=True)  
    return JsonResponse(serializer.data, safe=False)


class ShopOrderPagination(PageNumberPagination):
    page_size = 10  # Default items per page
    page_size_query_param = 'page_size'  # Allow client to set custom page size
    max_page_size = 100  # Maximum items per page

class ShopOrderViewSet(viewsets.ModelViewSet):
    queryset = ShopOrder.objects.all()
    serializer_class = ShopOrderSerializer
    permission_classes = [ReadOnlyUserPermission]
    pagination_class = ShopOrderPagination
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = ['account', 'order_status']
    search_fields = [
        'order_status',
        'address_street',
        'address_city',
        'client__phone',       # Search by client's phone
        'client__username',    # Search by client's name (username)
    ]
    def get_queryset(self):
        # Get the account_id from query parameters
        account_id = self.request.query_params.get('account_id', None)
        queryset = ShopOrder.objects.all()

        # If account_id is provided, filter by it
        if account_id is not None:
            queryset = queryset.filter(account_id=account_id)

        return queryset
    def get_serializer_class(self):
        # Use ShopOrderGetItemSerializer for GET requests (list/retrieve)
        if self.action in ['list', 'retrieve']:
            return ShopOrderGetSerializer
        # Use ShopOrderItemSerializer for other actions like create, update, and delete
        return ShopOrderSerializer