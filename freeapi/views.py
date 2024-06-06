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
