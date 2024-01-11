from .serializers import *
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import *
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout
from datetime import datetime
import json
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator

class MyObtainTokenPairView(TokenObtainPairView):

    permission_classes = (AllowAny,)
    serializer_class = MyTokenObtainPairSerializer


    def get(self, request):
        print("weweweweewew")
        return redirect('register')

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

def login_view(request):
    return render(request, 'accounts/sign-in.html')

def login_user(request):
    if request.method == "POST":
        # Accessing username and password from form data
        username = request.POST["username"]
        password = request.POST["password"]

        # Check if username and password are correct, returning User object if so
        user = authenticate(request, username=username, password=password)

        # If user object is returned, log in and route to index page:
        if user:
            login(request, user)
            return redirect('dashboard')
            #return HttpResponseRedirect(reverse("index"))
        # Otherwise, return login page again with new context
        else:
            return render(request, "accounts/sign-in.html", {
                "message": "Invalid Credentials"
            })
    return render(request, "accounts/sign-in.html")

def logout_view(request):
    logout(request)
    return render(request, "accounts/sign-in.html", {
                "message": "Logged Out"
            })

@login_required(login_url='loginUser')
def clients(request):

    account = Account.objects.get(user=request.user)

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')

        new_client = Clients(account=account,username=username, email=email, phone=phone)
        new_client.save()


    username = request.user.username
    clients = Clients.objects.filter(account=account)
    items_per_page = 10
    paginator = Paginator(clients, items_per_page)

    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'username': username,
        "page_obj": page_obj,
        "activeClient":"active"
    }

    return render(request, 'accounts/clients.html',context=context)



@login_required(login_url='loginUser')
def index(request):
    username = request.user.username
    
    account = Account.objects.get(user=request.user)
    orders = Order.objects.filter(account=account)
    reviews = Reviews.objects.filter(account=account)
    payments = Payment.objects.filter(account=account)
    offers = Offers.objects.filter(account=account)
    clients = Clients.objects.filter(account=account)

    ordersNum = float(len(orders))
    reviewsNum = float(len(reviews))
    offersNum = float(len(offers))
    
    if len(payments) == 0:   
        paymentAmount = 0
    else:
        paymentAmount = payments.amount


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
    orders_by_day = Order.objects.filter(date__gte=start_date).extra({'day': "date(date)"}).values('day').annotate(order_count=Count('id')).order_by('day')    
    for entry in orders_by_day:
        day_date_str = entry['day']  # Assuming 'day' is a string representation of the date
        day_date = datetime.strptime(day_date_str, '%Y-%m-%d')  # Convert string to datetime object
        day_number = day_date.weekday()  # Get the weekday number from the date
        day_name = day_names[day_number]
        stats[day_name] = entry['order_count']  # Map the number to the day name



    items_per_page = 10
    paginator = Paginator(clients, items_per_page)

    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)


    context = {
        "username":username,
        "ordersNum":ordersNum,
        "reviewsNum":reviewsNum,
        "paymentAmount": paymentAmount,
        "offersNum":offersNum,
        "clients": clients,
        "stats":stats,
        "monday": stats['Monday'],
        "Tuesday": stats['Tuesday'],
        "Wednesday": stats['Wednesday'],
        "Thursday": stats['Thursday'],
        "Friday": stats['Friday'],
        "Saturday": stats['Saturday'],
        "Sunday": stats['Sunday'],
        "page_obj":page_obj,
        "active":"active"
    }
    return render(request, 'accounts/index.html', context=context)


def menu(request):
    return render(request, 'accounts/menu.html')


@login_required(login_url='loginUser')
def order(request):
    account = Account.objects.get(user=request.user)

    username = request.user.username

    if request.method == 'POST':
      
        date = datetime.now()
        email = request.POST.get('email')
        username = request.POST.get('username')
        phone = request.POST.get('phone')
        price = request.POST.get('price')
        note = request.POST.get('note')
        item = request.POST.get('item')
        pay = request.POST.get('pay')
        quantity = request.POST.get('quantity')

        client = Clients.objects.filter(account=account, email=email)
    
        if len(client) == 0:
            new_client = Clients(account=account,username=username,numberOfOrders=1 ,email=email, phone=phone)
            new_client.save()

            newOrder = Order(price=price, date=date,note=note,client=new_client, account=account, item=item, quantity=quantity, pay=pay)
            newOrder.save()
        else:
            client = Clients.objects.get(account=account, email=email)
            client.numberOfOrders += 1
            client.save()

            newOrder = Order(price=price, date=date,note=note, client=client,account=account, item=item, quantity=quantity, pay=pay)
            newOrder.save()
        return redirect('thanks')

    elif request.method == 'PUT':
        raw_data = request.body.decode('utf-8')
        json_data = json.loads(raw_data)
        orderid = json_data.get('orderId')
        

        updatedOrder = Order.objects.get(account=account, id=int(orderid))
        print(updatedOrder)
        updatedOrder.status = 'Done'
        updatedOrder.save()
        return JsonResponse({'statue' : 'done'},status=200)   

    orders = Order.objects.filter(account=account)
    items_per_page = 10

    paginator = Paginator(orders, items_per_page)
    page_number = request.GET.get('page', 1)
    page_order_obj = paginator.get_page(page_number)


    context={
        "username":username,
        "activeOrder":"active",
        "page_order_obj":page_order_obj,
        "orders": orders
    }
    
    return render(request, 'accounts/orders.html',  context=context)


@login_required(login_url='loginUser')
def payment(request):
    username = request.user.username

    context={
        "username":username,
        "activePayment":"active"
    }

    return render(request, 'accounts/payment.html', context=context)


def thanks(request):
    return render(request, 'accounts/thanks.html')

@login_required(login_url='loginUser')
def edit_menu(request):
    username = request.user.username
    context={
        "username":username,
        "activemenu":"active"
    }
    return render(request, 'accounts/editMenu.html', context=context)


@login_required(login_url='loginUser')
def profile(request):
    current_user = request.user
    username = request.user.username

    if request.method == 'POST':
        user_to_update = User.objects.get(username=username)
        user_to_update.username = request.POST.get('username')
        user_to_update.first_name = request.POST.get('firstName')
        user_to_update.last_name = request.POST.get('lastName')
        user_to_update.email = request.POST.get('email')
        password = request.POST.get('passowrd')
        print(password)
        if request.POST.get('passowrd') == request.POST.get('passowrd2'):
            print("inside password")
            user_to_update.set_password()
        else:
            return "<p> password doesn't match </p>"

        user_to_update.save()
  

    context = {
        "username":username,
        "email": current_user.email,
        "firstName":current_user.first_name,
        "lastName":current_user.last_name
    }
    return render(request, 'accounts/profile.html', context=context)
