from django.urls import path, re_path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('dashboard', views.IndexView.as_view(), name='index'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('chart',views.ChartIndex.as_view(), name='Chart' ),
    path('lastClient',views.LastClientView.as_view(), name='lastClient' ),
    path('register', views.RegisterView.as_view(), name='register'),
    path('offers/<int:pk>', views.OfferDetailView.as_view(), name="offers"),
    path('offers', views.OfferDetailView.as_view(), name="Post offers"),
    path('items/<int:pk>', views.MenuItemDetailView.as_view(), name="menuItems"),
    path('items', views.MenuItemDetailView.as_view(), name="PostMenuItems")
]