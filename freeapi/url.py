from django.urls import path, re_path, include
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import routers

router = routers.DefaultRouter()
router.register('options',  
 views.OptionsViewSet)




urlpatterns = [
    path('dashboard', views.IndexView.as_view(), name='index'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('chart',views.ChartIndex.as_view(), name='Chart' ),
    path('lastClient',views.LastClientView.as_view(), name='lastClient' ),
    path('register', views.RegisterView.as_view(), name='register'),
    path('offers/<int:pk>', views.OfferDetailView.as_view(), name="offers"),
    path('items/<int:pk>/<int:itemId>', views.MenuItemDetailView.as_view(), name="offers"),
    path('offers', views.OfferDetailView.as_view(), name="Post offers"),
    path('items/<int:pk>', views.MenuItemDetailView.as_view(), name="menuItems"),
    path('items', views.MenuItemDetailView.as_view(), name="PostMenuItems"),
    path('', include(router.urls)),
    path('options/<int:account_id>/<int:menuitem_id>', views.get_items_by_account_and_menuitem),
]