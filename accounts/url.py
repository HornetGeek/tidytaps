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
    path('modifiers', modifiers, name='modifiers'),
    path('modifierEdit', modifierEdit, name='mofidierEdit'),
    path('modifierDelete', modifierDelete, name='modifierDelete'),
    path('size', size, name="size"),
    path('sizeEdit', sizeEdit, name="sizeEdit"),
    path('sizeDelete', sizeDelete, name="sizeDelete"),
    path('orders', order, name='orders'),
    path('addorders', add_order, name='orders'),
    path('addorders2', add_order2, name='orders2'),
    path('ordernow', order_now, name='ordernow'),
    path('ordernow2', order_now2, name='ordernow2'),
    path('profile', profile, name='profile'),
    path('index/', index, name='dashboard'),
    path('edit_Menu', edit_menu, name='edit_Menu'),
    path('order/<str:name>/', online, name='online'),
    path('category',category, name='category'),
    path('thanks', thanks, name='thanks'),
    path('menu', menu,name="menu"),
    path('logout/', logout_view, name="logout"),
    re_path(r'^menu/(?P<uuid>[0-9a-f-]+)$', listMenu, name='listMenu'),
    re_path(r'^menu/(?P<auuid>[0-9a-f-]+)/v2/$', proxy, name='proxy'),
    re_path(r'^menu/link/(?P<linkuuid>[0-9a-f-]+)/(?P<auuid>[0-9a-f-]+)/$', listMenuv2, name='listMenuv2'),
]