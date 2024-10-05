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

from accounts.models import Account, MenuItem, Category
from django.contrib.auth.models import User

# Start command - sends a welcome message and instructions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    context.user_data['chat_id'] = chat_id

    try:
        account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
        context.user_data['account'] = account

        welcome_message = (
            f"Welcome back, {account.username}! 🎉\n\n"
            "You can use the following commands:\n"
            "/add_product - Add a new product.\n"
            "/edit_product - Edit an existing product.\n"
            "/delete_product - Delete a product.\n"
        )
    except Account.DoesNotExist:
        welcome_message = (
            "Welcome! 🎉\n\n"
            "Use /add_account to create an account first."
        )
    await update.message.reply_text(welcome_message)

# Add account flow
async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Please send the username for the account.')
    context.user_data['state'] = 'awaiting_username'

# Product flow
async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    context.user_data['chat_id'] = chat_id
    account = context.user_data.get('account')
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.message.reply_text("You need to create an account first using /add_account.")
            return

    await update.message.reply_text('Please provide the category for the product.')
    context.user_data['state'] = 'awaiting_category'

# Edit product flow
async def edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    
    # Ensure account is fetched asynchronously
    try:
        account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
    except Account.DoesNotExist:
        await update.message.reply_text("You don't have an account yet.")
        return

    # Fetch products asynchronously
    products = await sync_to_async(MenuItem.objects.filter)(account=account)

    # Convert the QuerySet to a list (since this is inside an async context)
    products = await sync_to_async(list)(products)

    if not products:
        await update.message.reply_text("You don't have any products to edit.")
        return

    # List the products for the user to choose from
    product_list = "\n".join([f"{idx + 1}. {item.item}" for idx, item in enumerate(products)])
    await update.message.reply_text(f"Please select a product to edit by its number:\n\n{product_list}")

    # Store products in user_data for future access
    context.user_data['products'] = products
    context.user_data['state'] = 'awaiting_edit_choice'


# Handle product selection for editing
async def handle_edit_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = update.message.text

    try:
        product = await sync_to_async(MenuItem.objects.get)(id=product_id)
        context.user_data['product'] = product

        await update.message.reply_text(
            "What would you like to edit? Choose one:\n"
            "1. Name\n2. Price\n3. Description\n4. Image"
        )
        context.user_data['state'] = 'awaiting_edit_choice'
    except MenuItem.DoesNotExist:
        await update.message.reply_text("Invalid product ID. Please try again.")
        context.user_data['state'] = 'awaiting_product_choice'

# Handle editing the product
async def handle_edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    product = context.user_data.get('product')

    if choice == '1':
        await update.message.reply_text(f"Current name: {product.item}. Send the new name:")
        context.user_data['state'] = 'awaiting_new_name'
    elif choice == '2':
        await update.message.reply_text(f"Current price: {product.price}. Send the new price:")
        context.user_data['state'] = 'awaiting_new_price'
    elif choice == '3':
        await update.message.reply_text(f"Current description: {product.desc}. Send the new description:")
        context.user_data['state'] = 'awaiting_new_description'
    elif choice == '4':
        await update.message.reply_text("Send the new image:")
        context.user_data['state'] = 'awaiting_new_image'
    else:
        await update.message.reply_text("Invalid choice. Please try again.")
        context.user_data['state'] = 'awaiting_edit_choice'

# Handle name update
async def handle_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text
    product = context.user_data['product']
    product.item = new_name
    await sync_to_async(product.save)()

    await update.message.reply_text(f"Product name updated to: {new_name}")
    context.user_data.clear()

# Handle price update
async def handle_new_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_price = update.message.text
    if not new_price.isdigit():
        await update.message.reply_text("Invalid price. Please enter a numeric value.")
        return

    product = context.user_data['product']
    product.price = int(new_price)
    await sync_to_async(product.save)()

    await update.message.reply_text(f"Product price updated to: {new_price}")
    context.user_data.clear()

# Handle description update
async def handle_new_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_description = update.message.text
    product = context.user_data['product']
    product.desc = new_description
    await sync_to_async(product.save)()

    await update.message.reply_text(f"Product description updated to: {new_description}")
    context.user_data.clear()

# Handle product image update
async def handle_new_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Please upload an image.")
        return

    product_image_file = await update.message.photo[-1].get_file()
    product_image_path = f"static/img/items/{context.user_data['chat_id']}_updated_{int(time.time())}.jpg"
    await product_image_file.download_to_drive(product_image_path)

    product = context.user_data['product']
    product.picture = product_image_path
    await sync_to_async(product.save)()

    await update.message.reply_text("Product image updated successfully.")
    context.user_data.clear()

# Delete product flow
async def delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    
    # Fetch the account asynchronously
    try:
        account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
    except Account.DoesNotExist:
        await update.message.reply_text("You don't have an account yet.")
        return

    # Fetch products asynchronously
    products = await sync_to_async(MenuItem.objects.filter)(account=account)
    
    # Convert the QuerySet to a list
    products = await sync_to_async(list)(products)

    if not products:
        await update.message.reply_text("You don't have any products to delete.")
        return

    # List the products for the user to choose from
    product_list = "\n".join([f"{idx + 1}. {item.item}" for idx, item in enumerate(products)])
    await update.message.reply_text(f"Please select a product to delete by its number:\n\n{product_list}")

    # Store products in user_data for future access
    context.user_data['products'] = products
    context.user_data['state'] = 'awaiting_delete_choice'

# Handle product selection for deletion
async def handle_delete_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = update.message.text

    try:
        product = await sync_to_async(MenuItem.objects.get)(id=product_id)
        context.user_data['product'] = product

        await update.message.reply_text(
            f"Are you sure you want to delete '{product.item}'? (yes/no)"
        )
        context.user_data['state'] = 'awaiting_delete_confirmation'
    except MenuItem.DoesNotExist:
        await update.message.reply_text("Invalid product ID. Please try again.")
        context.user_data['state'] = 'awaiting_delete_choice'

# Handle delete confirmation
async def handle_delete_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_response = update.message.text.lower()

    if user_response == 'yes':
        product = context.user_data['product']
        await sync_to_async(product.delete)()

        await update.message.reply_text(f"Product '{product.item}' has been deleted.")
        context.user_data.clear()
    else:
        await update.message.reply_text("Deletion cancelled.")
        context.user_data.clear()

# Message handler for the account creation flow
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')

    if state == 'awaiting_username':
        username = update.message.text
        chat_id = context.user_data['chat_id']

        account, created = await sync_to_async(Account.objects.get_or_create)(
            telegramId=chat_id, defaults={'username': username}
        )

        if created:
            await update.message.reply_text(f"Account created successfully with username: {username}")
        else:
            await update.message.reply_text(f"Account already exists with username: {account.username}")
        context.user_data.clear()

    elif state == 'awaiting_category':
        category_name = update.message.text
        account = context.user_data['account']

        category, created = await sync_to_async(Category.objects.get_or_create)(
            account=account, name=category_name
        )

        context.user_data['category'] = category
        await update.message.reply_text('Please provide the name of the product.')
        context.user_data['state'] = 'awaiting_product_name'

    elif state == 'awaiting_product_name':
        product_name = update.message.text
        context.user_data['product_name'] = product_name
        await update.message.reply_text('Please provide the product description.')
        context.user_data['state'] = 'awaiting_product_description'

    elif state == 'awaiting_product_description':
        product_description = update.message.text
        context.user_data['product_description'] = product_description
        await update.message.reply_text('Please provide the product price.')
        context.user_data['state'] = 'awaiting_product_price'

    elif state == 'awaiting_product_price':
        product_price = update.message.text
        if not product_price.isdigit():
            await update.message.reply_text('Invalid price. Please enter a numeric value.')
            return

        context.user_data['product_price'] = int(product_price)
        await update.message.reply_text('Please upload a product image.')
        context.user_data['state'] = 'awaiting_product_image'

    elif state == 'awaiting_product_image':
        if not update.message.photo:
            await update.message.reply_text('Please upload an image.')
            return

        product_image_file = await update.message.photo[-1].get_file()
        product_image_path = f"static/img/items/{context.user_data['chat_id']}_{int(time.time())}.jpg"
        await product_image_file.download_to_drive(product_image_path)

        account = context.user_data['account']
        category = context.user_data['category']
        product_name = context.user_data['product_name']
        product_description = context.user_data['product_description']
        product_price = context.user_data['product_price']

        await sync_to_async(MenuItem.objects.create)(
            account=account,
            category=category,
            item=product_name,
            desc=product_description,
            price=product_price,
            picture=product_image_path
        )

        await update.message.reply_text(f"Product '{product_name}' added successfully!")
        context.user_data.clear()

    elif state == 'awaiting_product_choice':
        await handle_edit_selection(update, context)

    elif state == 'awaiting_edit_choice':
        await handle_edit_choice(update, context)

    elif state == 'awaiting_new_name':
        await handle_new_name(update, context)

    elif state == 'awaiting_new_price':
        await handle_new_price(update, context)

    elif state == 'awaiting_new_description':
        await handle_new_description(update, context)

    elif state == 'awaiting_new_image':
        await handle_new_image(update, context)

    elif state == 'awaiting_delete_choice':
        await handle_delete_selection(update, context)

    elif state == 'awaiting_delete_confirmation':
        await handle_delete_confirmation(update, context)

# Main function to setup the bot
def main():
    app = Application.builder().token("6977293897:AAE9OYhwEn75eI6mYyg9dK1_YY3hCB2M2T8").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_account", add_account))
    app.add_handler(CommandHandler("add_product", add_product))
    app.add_handler(CommandHandler("edit_product", edit_product))
    app.add_handler(CommandHandler("delete_product", delete_product))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Telegram Bot Started !!")
    app.run_polling()

if __name__ == "__main__":
    main()
