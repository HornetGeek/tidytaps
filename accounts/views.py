from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import *
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponse
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
from django.contrib import messages
from django.utils.translation import gettext as _
import random

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
            messages.error(request, 'Incorrect username or password. Please try again.')
            return render(request, "accounts/sign-in.html")

    return render(request, "accounts/sign-in.html")

def logout_view(request):
    logout(request)
    return render(request, "accounts/sign-in.html", {
                "messages": "Logged Out"
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
        "activeClient":"active",
        "account":account
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
    orders_by_day = Order.objects.filter(account=account,date__gte=start_date).extra({'day': "date(date)"}).values('day').annotate(order_count=Count('id')).order_by('day')   
    print(orders_by_day) 
    for entry in orders_by_day:
        day_date_str = entry['day']  # Assuming 'day' is a string representation of the date
        print(day_date_str)
        day_date = datetime.strptime(day_date_str, '%Y-%m-%d')  # Convert string to datetime object
        print(day_date)
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
        "active":"active",
        "account":account
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
        price = float(request.POST.get('price'))
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
    grouped_orders = {}
   
    orders_by_order_id = (
        Order.objects.filter(account=account)
        .values('orderId', 'status')
        .annotate(order_count=Count('orderId'))
    )
    print(orders_by_order_id)
    for order_data in orders_by_order_id:
        order_id = order_data['orderId']
        order_count = order_data['order_count']
        order_status = order_data['status']
        print(order_status)
        if order_status == 'waiting':
        # Fetch all Order objects with the same orderId
            orders_with_same_id = Order.objects.filter(account=account, orderId=order_id)

            # Store the list of orders in the dictionary
            grouped_orders[order_id] = orders_with_same_id
    print("grouped_orders")
    print(grouped_orders)
    items_per_page = 10

    paginator = Paginator(orders, items_per_page)
    page_number = request.GET.get('page', 1)
    page_order_obj = paginator.get_page(page_number)


    context={
        "username":username,
        "activeOrder":"active",
        "page_order_obj":page_order_obj,
        "orders": orders,
        "account":account
    }
    
    return render(request, 'accounts/orders.html',  context=context)

def generate_unique_order_id():
    while True:
        # Generate a random orderId
        order_id = random.randint(1000, 9999)  # Adjust the range as needed

        # Check if the orderId already exists in the database
        if not Order.objects.filter(orderId=order_id).exists():
            return order_id



def add_order(request):
    json_data = json.loads(request.body.decode('utf-8'))
    date = datetime.now()
    print(json_data)
    uuid = json_data[0]['uuid']

    email = json_data[0]['email']
    username = json_data[0]['name']
    phone = json_data[0]['phone']
    note = json_data[0]["note"]
    table = json_data[0]["table"]
    print(table)
    unique_order_id = generate_unique_order_id()

    account = Account.objects.get(accountId=uuid)
    client = Clients.objects.filter(account=account, phone=phone)
    print("lennnnnnnnn")
    print(len(client))
    if len(client) == 0:
        client = Clients(account=account,username=username,numberOfOrders=1 ,email=email, phone=phone)
        client.save()
    else:
        client = Clients.objects.get(account=account, phone=phone)
        client.numberOfOrders += 1
        client.save()

    for data in json_data:
        print(data['item'])
        item_id = data['item']['id']
        quantity = data['item']['quantity']
        #cupsize = data['item']['cupsize']
        if "modifiers" in data['item']:
            modifiers = data['item']['modifiers']
        else:
            modifiers = None

        if "cupsize" in data["item"]:
            size = data['item']['cupsize']
        else:
            size = ""
       
        if "modifier_note" in data['item']:
            modifiers_note = data['item']['modifier_note']
        else:
            modifiers_note = None
        
        item = MenuItem.objects.get(account=account,id=item_id)
        price = item.price
        
        newOrder = Order(item=item,price=price, date=date,note=note, client=client,account=account, size=size,quantity=quantity, orderId=unique_order_id,modifier=modifiers, modifier_note=modifiers_note, tableNum=int(table) )
        newOrder.save()
        import threading
        thread = threading.Thread(target=send_telegram_message, args=(table,account, item, price, date, note, size, quantity, modifiers, modifiers_note))
        thread.start()
        
    return JsonResponse({'status': 'success', 'order_id': unique_order_id})

def add_order2(request):
    try:
        print("add order22222")
        json_data = json.loads(request.body.decode('utf-8'))
        date = datetime.now()
        print(json_data)
        uuid = json_data[0]['uuid']
        auuid = json_data[0]['auuid']
        email = json_data[0]['email']
        username = json_data[0]['name']
        phone = json_data[0]['phone']
        note = json_data[0]["note"]
        table = json_data[0]["table"]
        print(table)
        unique_order_id = generate_unique_order_id()

        
        TempNewlink = "/menu/link/" + uuid + '/' + auuid +"?table="+table
        link = OneLink.objects.get(link=TempNewlink)

        account = Account.objects.get(accountId=link.account.accountId)
        account = Account.objects.get(accountId=link.account.accountId)
        client = Clients.objects.filter(account=account, phone=phone)

        if len(client) == 0:
            client = Clients(account=account,username=username,numberOfOrders=1 ,email=email, phone=phone)
            client.save()
        else:
            client = Clients.objects.get(account=account, phone=phone)
            client.numberOfOrders += 1
            client.save()
        print("wwwwwwwwwwwwwwwwww2")
        for data in json_data:
            print(data['item'])
            item_id = data['item']['id']
            quantity = data['item']['quantity']
            #cupsize = data['item']['cupsize']
            if "modifiers" in data['item']:
                modifiers = data['item']['modifiers']
            else:
                modifiers = None

            if "cupsize" in data["item"]:
                size = data['item']['cupsize']
            else:
                size = ""

            if "modifier_note" in data['item']:
                modifiers_note = data['item']['modifier_note']
            else:
                modifiers_note = None
            
            item = MenuItem.objects.get(account=account,id=item_id)
            price = item.price
            
            newOrder = Order(item=item,price=price, date=date,note=note, client=client,account=account, size=size,quantity=quantity, orderId=unique_order_id,modifier=modifiers, modifier_note=modifiers_note, tableNum=int(table) )
            newOrder.save()
            import threading
            thread = threading.Thread(target=send_telegram_message, args=(table,account,item.item, price,date,note,size,quantity,modifiers, modifiers_note))
            thread.start()
            link.delete()
            
        return JsonResponse({'status': 'success', 'order_id': unique_order_id})
    except Exception as e :
        print(e)
        return HttpResponse("link Expired, Rescan QR code", status=404)

def order_now(request):
    json_data = json.loads(request.body.decode('utf-8'))
    date = datetime.now()
    print(json_data)
    uuid = json_data[0]['uuid']
    
    username = "table " + str(json_data[0]['name'])
    note = json_data[0]["note"]
    table = json_data[0]["name"]

    print(table)
    unique_order_id = generate_unique_order_id()

    account = Account.objects.get(accountId=uuid)
    client = Clients.objects.filter(account=account,username=username)

    if len(client) == 0:
        client = Clients(account=account,username=username,numberOfOrders=1)
        client.save()
    else:
        client = Clients.objects.get(account=account,username=username)
        client.numberOfOrders += 1
        client.save()

    for data in json_data:
        print(data['item'])
        item_id = data['item']['id']
        quantity = data['item']['quantity']
        #cupsize = data['item']['cupsize']

        if "modifiers" in data['item']:
            modifiers = data['item']['modifiers']
        else:
            modifiers = None
        if "cupsize" in data["item"]:
            size = data['item']['cupsize']
        else:
            size = "NO Size"

        if "modifier_note" in data['item']:
            modifiers_note = data['item']['modifier_note']
        else:
            modifiers_note = None
        
        item = MenuItem.objects.get(account=account,id=item_id)
        price = item.price
        
        import threading
        thread = threading.Thread(target=send_telegram_message, args=(table,account,item, price, date, note, size, quantity, modifiers, modifiers_note))
        thread.start()

        newOrder = Order(item=item,price=price, date=date,note=note, client=client,account=account,size=size, quantity=quantity, orderId=unique_order_id,modifier=modifiers, modifier_note=modifiers_note, tableNum=int(table) )
        newOrder.save()
        
    return JsonResponse({'status': 'success', 'order_id': unique_order_id})

def order_now2(request):
    try:

        print("order_now 222222")
        print("request.body.decode('utf-8')")
        print(request.body)
        json_data = json.loads(request.body.decode('utf-8'))
        date = datetime.now()

        print("order_now 33333")
        print(json_data)
        uuid = json_data[0]['uuid']
        auuid = json_data[0]['auuid']
        username = "table " + str(json_data[0]['name'])
        note = json_data[0]["note"]
        table = json_data[0]["name"]

        print(table)
        unique_order_id = generate_unique_order_id()
        TempNewlink = "/menu/link/" + uuid + '/' + auuid +"?table="+table
        link = OneLink.objects.get(link=TempNewlink)
        account = Account.objects.get(accountId=link.account.accountId)
        
        client = Clients.objects.filter(account=account,username=username)

        if len(client) == 0:
            client = Clients(account=account,username=username,numberOfOrders=1)
            client.save()
        else:
            client = Clients.objects.get(account=account,username=username)
            client.numberOfOrders += 1
            client.save()

        for data in json_data:
            print(data['item'])
            item_id = data['item']['id']
            quantity = data['item']['quantity']
            #cupsize = data['item']['cupsize']

            if "modifiers" in data['item']:
                modifiers = data['item']['modifiers']
            else:
                modifiers = None
            if "cupsize" in data["item"]:
                size = data['item']['cupsize']
            else:
                size = "NO Size"

            if "modifier_note" in data['item']:
                modifiers_note = data['item']['modifier_note']
            else:
                modifiers_note = None
            
            item = MenuItem.objects.get(account=account,id=item_id)
            price = item.price
            print("wwwwwwwwwwwwwwwwwwwwwwwww")
            import threading
            thread = threading.Thread(target=send_telegram_message, args=(table,account,item, price,date,note,size,quantity,modifiers, modifiers_note))
            thread.start()

            newOrder = Order(item=item,price=price, date=date,note=note, client=client,account=account,size=size, quantity=quantity, orderId=unique_order_id,modifier=modifiers, modifier_note=modifiers_note, tableNum=int(table) )
            newOrder.save()
            link.delete()

            
        return JsonResponse({'status': 'success', 'order_id': unique_order_id})
    except Exception as e:
        print(e)
        return HttpResponse("link Expired, Rescan QR code", status=404)

def send_telegram_message(table,account, item, price,date,note,size,quantity,modifiers, modifiers_note):
    import requests
    # Replace 'YOUR_BOT_TOKEN' and 'YOUR_CHAT_ID' with your actual bot token and chat ID
    bot_token = '6977293897:AAE9OYhwEn75eI6mYyg9dK1_YY3hCB2M2T8'
    #chat_id = '1281643104'
    chat_id = account.telegramId
    print(chat_id)
    api_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

    # Message content
    message_text = f' New Order from Table  {str(table)} \n \n Item : {str(item)} \n  Extra: {str(modifiers)} \n Size : {str(size)} \n Quantity : {str(quantity)} \n Note : {str(note)} \n Price: {str(price)} \n Date: {str(date)}' 

        # Send the message using a POST request
    params = {
        'chat_id': chat_id,
        'text': message_text,
    }

    response = requests.post(api_url, params=params)

          # Check if the request was successful
    if response.ok:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message. Response content: {response.content}")

def online(request, name):
    print(name)
    account = Account.objects.get(username=name)
    print(account)
    menu = Menu.objects.get(account=account)
  
    menuTitle = menu.title
   
    logo = menu.logo
    
    categories = menu.category_menu.all()
    menuitems = MenuItem.objects.filter(account=account, category__in=menu.category_menu.all())
    modifiers = Modifier.objects.filter(account=account)

    sizemodifier = SizeModifier.objects.filter(account=account)
    
    print(menuitems)

    context = {
        "menuTitle": menuTitle,
        "logo" : str(str(logo).split("static")[1]),
        "categories": categories,
        "items":menuitems,
        "modifiers":modifiers,
        "account":account,
        "sizemodifier":sizemodifier 
    }
    return render(request, 'accounts/online-order.html', context=context)

@login_required(login_url='loginUser')
def payment(request):
    username = request.user.username
    account = Account.objects.get(user=request.user)
    context={
        "username":username,
        "activePayment":"active",
        "account":account
    }

    return render(request, 'accounts/payment.html', context=context)


@login_required(login_url='loginUser')
def category(request):
    username = request.user.username
    account = Account.objects.get(user=request.user)
    menu = Menu.objects.get(account=account)
    name = request.POST.get('name')
    category = Category(account=account,menu=menu,name=name)

    if request.method == 'POST':
        
        category.save()

    return redirect('edit_Menu')


def thanks(request):
    order_id = request.GET.get('orderId', None)
    if order_id is not None:
        context={
        "orderId":order_id,
        }
        return render(request, 'accounts/thanks.html', context=context)
    else:
        return render(request, 'accounts/thanks.html')

@login_required(login_url='loginUser')
def edit_menu(request):
    username = request.user.username
    account = Account.objects.get(user=request.user)
    print("logging accound id ")
    accountId = account.accountId
    print(account.accountId)
    try:
        menu = Menu.objects.get(account=account)
        categories = menu.category_menu.all()
        print(categories)
    except Exception as e:
        menu = []
        categories = []
        print(e)
        pass

    try:
        items = account.MenuItem_account.all()
        print(items)
    except Exception as e:
        items = []
        print(e)

    try:
        modifiers = Modifier.objects.filter(account=account, menuitem__in=items)
        print(modifiers)
    except Exception as e:
        modifiers = []
        print(e)

    try:
        sizes = SizeModifier.objects.filter(account=account, menuitem__in=items)
    except Exception as e:
        sizes = []
        print(e)  

    if request.method == 'POST':
        title = request.POST.get('title', '')
        logo = request.FILES['logo']
        menu = Menu.objects.filter(account=account)

        if menu.exists():
            context={
                "username":username,
                "activemenu":"active", 
                "categories":categories,
                "items":items,
                'error_message': "You have already menu",
                "menu":menu,
                "accountId": accountId,
                "account":account,
                "sizes":sizes
            }
            return render(request, 'accounts/editMenu.html', context=context)
            print("menu is exists")
        else:
            menu = Menu.objects.create(account=account,logo=logo, title=title)
    

    context={
        "username":username,
        "activemenu":"active",
        "categories":categories,
        "items":items,
        "menu":menu,
        "modifiers":modifiers,
        "accountId":accountId,
        "account":account,
        "sizes":sizes
        
    }
    print(sizes)
    return render(request, 'accounts/editMenu.html', context=context)


@login_required(login_url='loginUser')
def editMenu(request):
    username = request.user.username
    account = Account.objects.get(user=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title', '')
        

        menu = Menu.objects.get(account=account)

        menu.title = title

        if "logo" in request.FILES:
            logo = request.FILES['logo']
        
            menu.logo = logo

        menu.save()

    return redirect('edit_Menu')

@login_required(login_url='loginUser')
def categoryEdit(request):

    username = request.user.username
    account = Account.objects.get(user=request.user)
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('id')
        print(category_id)

        category = Category.objects.get(id=str(category_id))

        category.name = name

        category.save()
    return redirect('edit_Menu')
    

@login_required(login_url='loginUser')
def categoryDelete(request):
    username = request.user.username
    account = Account.objects.get(user=request.user)
    if request.method == 'POST':
        category_id = request.POST.get('id')
        print(category_id)

        category = Category.objects.get(id=str(category_id))

        category.delete()

    return redirect('edit_Menu')


@login_required(login_url='loginUser')
def item(request):
    account = Account.objects.get(user=request.user)

    menu = Menu.objects.get(account=account)
    
    if request.method == 'POST':
            
        name = request.POST.get('name')
        price = request.POST.get('price')
        desc = request.POST.get('desc')

        
        pic = request.FILES['pic']
       
        category_name = request.POST.get('category')
        print(menu)
        category = Category.objects.get(menu=menu,name=category_name)
        print(category)
        try :
            menuItems = MenuItem.objects.get(category=category)
        except Exception as e:
            menuItems = []
        Item = MenuItem(account=account,category=category, item=name, price=price, desc=desc, picture=pic )
        Item.save()
        print(menu.category_menu.all()) 
        print(menu.title)

    elif request.method == 'GET':
        try:
            menu = Menu.objects.get(account=account)
            categories = menu.category_menu.all()
            print(categories)
        except Exception as e:
            menu = []
            categories = []
            print(e)
            pass
        context = {
            "categories":categories
        }
        return render(request, 'accounts/item.html', context=context)
    return redirect('edit_Menu')

@login_required(login_url='loginUser')
def itemEdit(request):
    account = Account.objects.get(user=request.user)

    if request.method == 'POST':
        print("weeeeeeeeeeee")
        name = request.POST.get('name')
        price = request.POST.get('price')
        desc = request.POST.get('desc')
        itemId = request.POST.get('id')
        category_name = request.POST.get('category')
        menu = Menu.objects.get(account=account)
        category = Category.objects.get(menu=menu,name=category_name)
        
        try :
            menuItems = MenuItem.objects.get(id=itemId)
        except Exception as e:
            menuItems = []

        menuItems.item = name
        menuItems.category = category
        menuItems.price = price
        menuItems.desc = desc
        if 'pic' in request.FILES:
            pic = request.FILES['pic']
            menuItems.picture = pic
        print(price)
        print(menuItems.save())
        

    return redirect('edit_Menu')

@login_required(login_url='loginUser')
def itemDelete(request):
    account = Account.objects.get(user=request.user)
    if request.method == 'POST':
        itemId = request.POST.get('id')
        menuItem = MenuItem.objects.get(id=str(itemId))

        menuItem.delete()

    return redirect('edit_Menu')

@login_required(login_url='loginUser')
def modifiers(request):
    account = Account.objects.get(user=request.user)
    menu = Menu.objects.get(account=account)

    categories = menu.category_menu.all()
    #menuitems = MenuItem.objects.get(account=account, category__in=menu.category_menu.all())
    if request.method == 'POST':
        item = request.POST.get('Item')
        name = request.POST.get('name')
        price = request.POST.get('price')
        if 'pic' in request.FILES:
            pic = request.FILES['pic']
        else:
            pic = ''
        print(item)
        menuItem = MenuItem.objects.get(account=account, item=item)
        modifier = Modifier(account=account, menuitem=menuItem, name=name, pic=pic, price=price )
        modifier.save()
    return redirect('edit_Menu')

@login_required(login_url='loginUser')
def modifierEdit(request):
    account = Account.objects.get(user=request.user)
    if request.method == 'POST':
        item = request.POST.get('item')
        menuItem = MenuItem.objects.get(account=account, item=item)

        modifierId = request.POST.get('id')
        name = request.POST.get('name')
        price = request.POST.get('price')
        modifier = Modifier.objects.get(id=modifierId, account=account)
        if 'pic' in request.FILES:
            pic = request.FILES['pic']
            modifier.pic = pic


        
        modifier.menuitem = menuItem
        modifier.price = price
        modifier.name = name
        modifier.save()
        print("modifissss")
        print(modifier)
    return redirect('edit_Menu')

@login_required(login_url='loginUser')
def modifierDelete(request):
    account = Account.objects.get(user=request.user)
    if request.method == 'POST':
        modifierId = request.POST.get('id')
        modifier = Modifier.objects.get(id=modifierId, account=account)
        modifier.delete()

    return redirect('edit_Menu')

@login_required(login_url='loginUser')
def size(request):
    account = Account.objects.get(user=request.user)
    menu = Menu.objects.get(account=account)

    categories = menu.category_menu.all()
    if request.method == 'POST':
        item = request.POST.get('Item')
        name = request.POST.get('name')
        price = request.POST.get('price')
        menuItem = MenuItem.objects.get(account=account, item=item)
        size = SizeModifier(account=account, menuitem=menuItem, size=name,price=price )
        size.save()
    return redirect('edit_Menu')

@login_required(login_url='loginUser')
def sizeEdit(request):
    account = Account.objects.get(user=request.user)
    if request.method == 'POST':
        item = request.POST.get('item')
        print(item)

        menuItem = MenuItem.objects.get(account=account, item=item)
        print(menuItem)
        sizeId = request.POST.get('id')
        name = request.POST.get('name')
        price = request.POST.get('price')
        size = SizeModifier.objects.get(id=sizeId, account=account)

        size.menuitem = menuItem
        size.price = price
        size.size = name
        size.save()
    return redirect('edit_Menu')

@login_required(login_url='loginUser')    
def sizeDelete(request):
    account = Account.objects.get(user=request.user)
    if request.method == 'POST':
        sizeId = request.POST.get('id')
        size = SizeModifier.objects.get(id=sizeId, account=account)
        size.delete()

    return redirect('edit_Menu')


def listMenu(request, uuid):
    

    print(uuid)
    account = Account.objects.get(accountId=uuid)
    print(account)
    menu = Menu.objects.get(account=account)
  
    menuTitle = menu.title
   
    logo = menu.logo
    
    categories = menu.category_menu.all()
    menuitems = MenuItem.objects.filter(account=account, category__in=menu.category_menu.all())
    modifiers = Modifier.objects.filter(account=account)

    sizemodifier = SizeModifier.objects.filter(account=account)
    
    print(menuitems)

    context = {
        "menuTitle": menuTitle,
        "logo" : str(str(logo).split("static")[1]),
        "categories": categories,
        "items":menuitems,
        "modifiers":modifiers,
        "account":account,
        "sizemodifier":sizemodifier 
    }
    return render(request, 'accounts/menu.html', context=context)

def proxy(request,auuid):
    try:
        print(auuid)
        account = Account.objects.get(accountId=auuid)

        domain = request.META['HTTP_HOST']
        print(domain)

        table = request.GET.get('table')

        unique_id = uuid.uuid4()


        TempNewlink = "/menu/link/" + str(unique_id) + '/' + auuid +"?table="+table
        print(TempNewlink)
        
        onelink = OneLink(account=account, link=TempNewlink)
        onelink.save()
        print(account)
        return redirect(TempNewlink)
    except Exception as e :
        print(e)
        return HttpResponse("link Expired, Rescan QR code")
    

def listMenuv2(request,linkuuid ,auuid):
    try:
        print(linkuuid)
        table = request.GET.get('table')
        TempNewlink = "/menu/link/" + linkuuid + '/' + auuid + "?table="+table
        link = OneLink.objects.get(link=TempNewlink)
        print(link.account.accountId)

        account = Account.objects.get(accountId=link.account.accountId)

        menu = Menu.objects.get(account=account)
    
        menuTitle = menu.title
    
        logo = menu.logo
        
        categories = menu.category_menu.all()
        menuitems = MenuItem.objects.filter(account=account, category__in=menu.category_menu.all())
        modifiers = Modifier.objects.filter(account=account)

        sizemodifier = SizeModifier.objects.filter(account=account)
        
        print(menuitems)

        context = {
            "menuTitle": _(menu.title),
            "logo" : str(str(logo).split("static")[1]),
            "categories": categories,
            "items":menuitems,
            "modifiers":modifiers,
            "account":account,
            "sizemodifier":sizemodifier 
        }
        return render(request, 'accounts/menu2.html', context=context)
    except Exception as e :
        print(e)
        return HttpResponse("link Expired, Rescan QR code")

@login_required(login_url='loginUser')
def profile(request):
    account = Account.objects.get(user=request.user)

    current_user = request.user
    username = request.user.username

    if request.method == 'POST':
        user_to_update = User.objects.get(username=username)
        user_to_update.username = request.POST.get('username')
        if "email" in request.POST:
            user_to_update.email = request.POST.get('email')
            messages.success(request, 'Your information was successfully updated!')
        if "password" in request.POST:
            
            print("insice passsssowd ")
            password = request.POST.get('password')
            if password == '':
                pass
            else:
                print(password)
                if request.POST.get('password') == request.POST.get('password2'):
                    print("inside password2222222")
                    user_to_update.set_password(password)
                    messages.success(request, 'Your password was successfully updated!')
                else:
                    return "<p> password doesn't match </p>"
        else:
            print("can't catch ")
            
        user_to_update.save()
        return redirect('profile')
  

    context = {
        "username":username,
        "email": current_user.email,
        "account":account
    }
    return render(request, 'accounts/profile.html', context=context)
