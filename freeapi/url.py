from django.urls import path, re_path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    
]