from django.urls import path, re_path, include
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import routers

router = routers.DefaultRouter()
router.register('choices',  views.MenuItemOptionsViewSet)

router2 = routers.DefaultRouter()
router2.register('options',  views.MenuOptionsViewSet)


router3 = routers.DefaultRouter()
router3.register(r'menuitem-photos', views.MenuItemPhotoViewSet, basename='menuitemphoto')



urlpatterns = [
    path('accounts/', views.AccountCreateAPIView.as_view(), name='account-create'),
    path('accounts/username/<str:username>/', views.AccountRetrieveByUsernameAPIView.as_view(), name='account-retrieve-by-username'),
    path('accounts/id/<int:id>/', views.AccountUpdateAPIView.as_view(), name='account-update'),  # Account by ID
    path('contacts/', views.ContactsListCreateAPIView.as_view(), name='contacts-list-create'),
    path('contacts/<int:account_id>/', views.ContactsListCreateAPIView.as_view(), name='contacts-list-create'),
    path('contacts/<int:account_id>/<int:pk>/', views.ContactsRetrieveUpdateDestroyAPIView.as_view(), name='contacts-detail'),
    path('delivery/account_id/<str:account_id>/', views.DeliveryByAccountIdView.as_view(), name='get_delivery_by_account_id'),
    path('delivery/username/<str:username>/', views.DeliveryByUsernameView.as_view(), name='get_delivery_by_username'),
    # Adresses
    path('adresses/', views.AdressesListCreateAPIView.as_view(), name='adresses-list-create'),
    path('adresses/<int:account_id>/', views.AdressesListCreateAPIView.as_view(), name='adresses-list-create'),
    path('adresses/<int:account_id>/<int:pk>/', views.AdressesRetrieveUpdateDestroyAPIView.as_view(), name='adresses-detail'),

    # SocialMedia
    path('social-media/', views.SocialMediaListCreateAPIView.as_view(), name='social-media-list-create'),
    path('social-media/<int:account_id>/', views.SocialMediaListCreateAPIView.as_view(), name='social-media-list-create'),
    path('social-media/<int:account_id>/<int:pk>/', views.SocialMediaRetrieveUpdateDestroyAPIView.as_view(), name='social-media-detail'),

    path('dashboard', views.IndexView.as_view(), name='index'),
    path('category',views.CategoryAPIView.as_view(), name='category'),
    path('category/<int:account_id>/', views.CategoryGetAPIView.as_view(), name='category-get'),
    path('categories/<int:account_id>/', views.CategoryWithItemsAPIView.as_view(), name='categories-with-items'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('chart',views.ChartIndex.as_view(), name='Chart' ),
    path('lastClient',views.LastClientView.as_view(), name='lastClient' ),
    path('register', views.RegisterView.as_view(), name='register'),
    path('offers/<int:pk>', views.OfferDetailView.as_view(), name="offers"),
    path('offers', views.OfferDetailView.as_view(), name="Post offers"),
    path('order',views.MakeOrderView.as_view()),
    path('items/<int:pk>', views.MenuItemDetailView.as_view(), name="menuItems"),
    path('items/<int:pk>/<int:itemId>', views.MenuItemDetailView.as_view(), name="items"),
    path('items', views.MenuItemDetailView.as_view(), name="PostMenuItems"),
    path('', include(router.urls)),
    path('', include(router2.urls)),
    path('', include(router3.urls)),
    path('menuitem-photos/account/menuitem/<int:account_id>/<int:menuitem_id>/', views.MenuItemPhotoListByAccountAndMenuItemView.as_view(), name='menuitem-photos-by-account-menuitem'),
    path('option/<int:account_id>/<int:menuitem_id>/', views.get_option_by_account_and_menuitem),
    path('choices/<int:account_id>/<int:menuitem_id>/<int:option_id>', views.get_items_by_account_and_menuitem),
]