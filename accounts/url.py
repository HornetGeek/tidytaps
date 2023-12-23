from django.urls import path
from . import views
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login/', MyObtainTokenPairView.as_view(), name='token_obtain_pair'),
    path('', login_view, name='login'),
    path('loginUser',login_user, name='loginUser'),
    path('clients', clients, name='clients'),
    path('payment', payment, name='payment'),
    path('orders', order, name='orders'),
    path('profile', profile, name='profile'),
    path('index/', index, name='dashboard'),
    path('editMenu', edit_menu, name='editMenu'),
    path('thanks', thanks, name='thanks'),
    path('menu', menu,name="menu"),
    path('logout/', logout_view, name="logout"),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='auth_register'),
]