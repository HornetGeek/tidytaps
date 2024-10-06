# Import necessary libraries and modules
import os
import sys
import django
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from asgiref.sync import sync_to_async
import re
import time
import qrcode
from io import BytesIO

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
        account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
        context.user_data['account'] = account  # Cache the account for future use
        welcome_message = f"Welcome back, {account.username}! 🎉\n\n"
        
        # No Add Account button since the account already exists
        keyboard = [
            [InlineKeyboardButton("Add Product", callback_data="add_product")]
        ]
    except Account.DoesNotExist:
        welcome_message = "Welcome to the bot! 🎉\n\n"
        
        # Show Add Account button since no account exists
        keyboard = [
            [InlineKeyboardButton("Add Account", callback_data="add_account")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_message + "You can use the following commands:", 
        reply_markup=reply_markup
    )
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

    chat_id = context.user_data.get('chat_id', update.message.chat.id)
    context.user_data['chat_id'] = chat_id  # Cache chat ID

    try:
        logo_file = await update.message.photo[-1].get_file()
        logo_path = f"static/img/logos/{chat_id}_logo.jpg"
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
        await update.message.reply_text("Invalid phone number. Please enter a valid phone number in the format 01XXXXXXXXX.")
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
    # Check if the update is a message or a callback query
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text("Unable to determine chat ID.")
        return

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

    # Now use the correct update object to reply
    if update.message:
        await update.message.reply_text('Please provide the category for the product.')
    else:
        await update.callback_query.message.reply_text('Please provide the category for the product.')

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
        await handle_category_confirmation(update, context)

# Handle category creation confirmation
async def handle_category_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category_name = context.user_data['category_name']
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="yes"),
            InlineKeyboardButton("No", callback_data="no"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Category '{category_name}' does not exist for this account. Do you want to create it?",
        reply_markup=reply_markup
    )

# Handle button clicks
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "add_account":
        await add_account(update, context)

    elif query.data == "add_product":
        await add_product(update, context)

    elif query.data == "yes":
        account = context.user_data.get('account')
        category_name = context.user_data['category_name']
        new_category = Category(name=category_name, account=account)
        await sync_to_async(new_category.save)()
        context.user_data['category'] = new_category

        await query.message.reply_text(
            text=f"Category '{category_name}' created successfully! Please provide the item name."
        )
        context.user_data['state'] = 'awaiting_item_name'

    elif query.data == "no":
        await query.message.reply_text(text='Category creation canceled. Please provide an existing category.')
        context.user_data['state'] = 'awaiting_category'


# Main function to start the bot
if __name__ == '__main__':
    token = "6977293897:AAE9OYhwEn75eI6mYyg9dK1_YY3hCB2M2T8"  # Replace with your bot token
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_account", add_account))
    application.add_handler(CommandHandler("add_product", add_product))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_click))
    print("Telegram Bot Started !!")
    application.run_polling()
