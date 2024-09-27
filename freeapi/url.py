from django.urls import path, re_path, include
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import routers

router = routers.DefaultRouter()
router.register('choices',  views.MenuItemOptionsViewSet)

router2 = routers.DefaultRouter()
router2.register('options',  views.MenuOptionsViewSet)




urlpatterns = [
    path('accounts/', views.AccountCreateAPIView.as_view(), name='account-create'),
    path('dashboard', views.IndexView.as_view(), name='index'),
    path('category',views.CategoryAPIView.as_view(), name='category'),
    path('category/<int:account_id>/', views.CategoryGetAPIView.as_view(), name='category-get'),
    path('categories/<int:account_id>/', views.CategoryWithItemsAPIView.as_view(), name='categories-with-items'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('chart',views.ChartIndex.as_view(), name='Chart' ),
    path('lastClient',views.LastClientView.as_view(), name='lastClient' ),
    path('register', views.RegisterView.as_view(), name='register'),
    path('offers/<int:pk>', views.OfferDetailView.as_view(), name="offers"),
    path('items/<int:pk>/<int:itemId>', views.MenuItemDetailView.as_view(), name="offers"),
    path('offers', views.OfferDetailView.as_view(), name="Post offers"),
    path('order',views.MakeOrderView.as_view()),
    path('items/<int:pk>', views.MenuItemDetailView.as_view(), name="menuItems"),
    path('items', views.MenuItemDetailView.as_view(), name="PostMenuItems"),
    path('', include(router.urls)),
    path('', include(router2.urls)),
    path('option/<int:account_id>/<int:menuitem_id>/', views.get_option_by_account_and_menuitem),
    path('choices/<int:account_id>/<int:menuitem_id>/<int:option_id>', views.get_items_by_account_and_menuitem),
]