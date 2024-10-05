import os
import sys
import django
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from asgiref.sync import sync_to_async
import re
import time

# Add the project root to sys.path so Python can find 'tidytap'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tidytap.settings')
django.setup()

# Now you can import your models
from accounts.models import Account, MenuItem, Category
from django.contrib.auth.models import User

# Start command - sends a welcome message and instructions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    context.user_data['chat_id'] = chat_id

    try:
        # Check if there's an account associated with this chat ID (telegramId)
        account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
        context.user_data['account'] = account  # Cache the account for future use

        # Personalized welcome message for existing account
        welcome_message = (
            f"Welcome back, {account.username}! 🎉\n\n"
            "You can use the following commands:\n"
            "/add_product - Add a new product by providing details like category, item name, price, description, and image.\n"
            "\nFeel free to start by typing /add_product."
        )

    except Account.DoesNotExist:
        welcome_message = (
            "Welcome to the bot! 🎉\n\n"
            "You can use the following commands:\n"
            "/add_account - Add a new account by providing details like username, logo, title, and phone number.\n"
            "/add_product - Add a new product by providing details like category, item name, price, description, and image.\n"
            "\nStart by typing /add_account to begin adding a new account."
        )

    await update.message.reply_text(welcome_message)

# Add account flow
async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Please send the username for the account.')
    context.user_data['state'] = 'awaiting_username'

# Handle messages (general handler to manage flow state)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state = context.user_data.get('state')

    if user_state == 'awaiting_username':
        await handle_username(update, context)
    elif user_state == 'awaiting_logo':
        await handle_logo(update, context)
    elif user_state == 'awaiting_title':
        await handle_title(update, context)
    elif user_state == 'awaiting_phone':
        await handle_phone(update, context)
    elif user_state == 'awaiting_category':
        await handle_category(update, context)
    elif user_state == 'awaiting_item_name':
        await handle_item_name(update, context)
    elif user_state == 'awaiting_price':
        await handle_price(update, context)
    elif user_state == 'awaiting_description':
        await handle_description(update, context)
    elif user_state == 'awaiting_image':
        await handle_product_image(update, context)
    elif user_state == 'awaiting_category_confirmation':
        await handle_category_confirmation(update, context)
    else:
        await update.message.reply_text("I don't understand that command. Use /add_product or /add_account to begin.")

# Handle account username step
async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text
    context.user_data['username'] = username
    await update.message.reply_text('Now please send the logo (as an image).')
    context.user_data['state'] = 'awaiting_logo'

# Handle account logo step
async def handle_logo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text('Please upload an image as the logo.')
        return
    
    await update.message.reply_text('Downloading your logo, this may take a few moments...')

    try:
        logo_file = await update.message.photo[-1].get_file()
        logo_path = f"static/img/logos/{context.user_data['chat_id']}_logo.jpg"
        await logo_file.download_to_drive(logo_path)
        await update.message.reply_text('Logo downloaded successfully.')

        context.user_data['logo'] = logo_path
        await update.message.reply_text('Now please send the title for the account.')
        context.user_data['state'] = 'awaiting_title'

    except Exception as e:
        await update.message.reply_text(f'An error occurred while downloading the logo: {str(e)}')

# Handle account title step
async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text
    context.user_data['title'] = title
    await update.message.reply_text('Finally, please send the phone number for the account.')
    context.user_data['state'] = 'awaiting_phone'

# Handle account phone number step
async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_number = update.message.text
    phone_pattern = r'^01[0-9]{9}$'

    if not re.match(phone_pattern, phone_number):
        await update.message.reply_text("Invalid phone number. Please enter a valid phone number in the format 012XXXXXXXX.")
        return

    context.user_data['phone_number'] = phone_number

    try:
        user = await sync_to_async(User.objects.get)(id=1)
    except User.DoesNotExist:
        await update.message.reply_text("User with ID 1 does not exist.")
        return

    account_data = {
        'user': user,
        'username': context.user_data['username'],
        'logo': context.user_data['logo'],
        'title': context.user_data['title'],
        'phone_number': context.user_data['phone_number'],
        'telegramId': context.user_data['chat_id'],
    }

    new_account = Account(**account_data)
    await sync_to_async(new_account.save)()

    await update.message.reply_text(
        '🎉 Account added successfully!\n\n'
        'You can now add a new product for your account by typing /add_product.\n'
        'Follow the prompts to specify the product category, name, price, description, and image.'
    )

    context.user_data.clear()

# Product flow
async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    account = context.user_data.get('account')
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            await update.message.reply_text("You need to create an account first using /add_account.")
            return

    await update.message.reply_text('Please provide the category for the product.')
    context.user_data['state'] = 'awaiting_category'

# Handle product category step
async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category_name = update.message.text
    account = context.user_data.get('account')

    try:
        category = await sync_to_async(Category.objects.get)(name=category_name, account=account)
        context.user_data['category'] = category
        await update.message.reply_text('Please provide the item name.')
        context.user_data['state'] = 'awaiting_item_name'

    except Category.DoesNotExist:
        context.user_data['category_name'] = category_name
        await update.message.reply_text(
            f"Category '{category_name}' does not exist for this account. Do you want to create it? (yes/no)"
        )
        context.user_data['state'] = 'awaiting_category_confirmation'

# Handle category creation confirmation
async def handle_category_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_response = update.message.text.lower()
    account = context.user_data.get('account')

    if user_response == 'yes':
        category_name = context.user_data['category_name']
        new_category = Category(name=category_name, account=account)
        await sync_to_async(new_category.save)()
        context.user_data['category'] = new_category
        await update.message.reply_text(f"Category '{category_name}' created successfully! Please provide the item name.")
        context.user_data['state'] = 'awaiting_item_name'
    elif user_response == 'no':
        await update.message.reply_text('Category creation canceled. Please provide an existing category.')
        context.user_data['state'] = 'awaiting_category'
    else:
        await update.message.reply_text("Please respond with 'yes' or 'no'. Do you want to create the category?")
        context.user_data['state'] = 'awaiting_category_confirmation'

# Handle item name step
async def handle_item_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    item_name = update.message.text
    context.user_data['item_name'] = item_name
    await update.message.reply_text('Please provide the price for the product.')
    context.user_data['state'] = 'awaiting_price'

# Handle price step
async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = update.message.text

    if not price.isdigit():
        await update.message.reply_text("Invalid price. Please enter a numeric value.")
        return

    context.user_data['price'] = int(price)
    await update.message.reply_text('Please provide a description for the product.')
    context.user_data['state'] = 'awaiting_description'

# Handle description step
async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text
    context.user_data['description'] = description  # Store the description for the next step
    await update.message.reply_text('Please send an image of the product.')
    context.user_data['state'] = 'awaiting_image'

# Handle product image step
async def handle_product_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text('Please upload an image of the product.')
        return

    await update.message.reply_text('Downloading your product image, this may take a few moments...')

    try:
        product_image_file = await update.message.photo[-1].get_file()
        product_image_path = f"static/img/items/{context.user_data['chat_id']}_product_{int(time.time())}.jpg"
        await product_image_file.download_to_drive(product_image_path)
        await update.message.reply_text('Product image downloaded successfully.')

        # Now save the menu item with all the information
        account = context.user_data['account']
        menu_item_data = {
            'account': account,
            'item': context.user_data['item_name'],
            'price': context.user_data['price'],
            'desc': context.user_data['description'],
            'category': context.user_data['category'],
            'picture': product_image_path  # Save the image path here
        }

        menu_item = MenuItem(**menu_item_data)
        await sync_to_async(menu_item.save)()
        
        username = account.username  # Get the username from the cached account
        website_url = f"https://tidytaps-r92c.vercel.app/f/{username}"
        await update.message.reply_text(
                f"🎉 Product '{menu_item.item}' added successfully! You can add another product by typing /add_product.\n"
                f"Visit your product page at: {website_url}"
            )
        # Clear user data for the next flow
        context.user_data.clear()

    except Exception as e:
        await update.message.reply_text(f'An error occurred while downloading the product image: {str(e)}')

# Main function to start the bot
if __name__ == '__main__':
    application = Application.builder().token('6977293897:AAE9OYhwEn75eI6mYyg9dK1_YY3hCB2M2T8').build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_account", add_account))
    application.add_handler(CommandHandler("add_product", add_product))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))  # Add this line to handle photo uploads
    print("Telegram Bot Started !!")
    application.run_polling()
