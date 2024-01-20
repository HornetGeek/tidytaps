from django.urls import path, re_path
from . import views
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('', login_view, name='login'),
    path('loginUser',login_user, name='loginUser'),
    path('clients', clients, name='clients'),
    path('editMenu', editMenu, name='editMenu'),
    path('categoryEdit', categoryEdit, name='categoryEdit'),
    path('categoryDelete', categoryDelete, name='categoryDelete'),
    path('itemEdit', itemEdit, name='itemEdit'),
    path('item', item, name='item'),
    path('itemDelete', itemDelete, name='itemDelete'),
    path('payment', payment, name='payment'),
    path('orders', order, name='orders'),
    path('profile', profile, name='profile'),
    path('index/', index, name='dashboard'),
    path('edit_Menu', edit_menu, name='edit_Menu'),
    path('category',category, name='category'),
    path('thanks', thanks, name='thanks'),
    path('menu', menu,name="menu"),
    path('logout/', logout_view, name="logout"),
    re_path(r'^menu/(?P<uuid>[0-9a-f-]+)$', listMenu, name='listMenu'),
]