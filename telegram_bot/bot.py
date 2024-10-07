# Import necessary libraries and modules
import os
import sys
import django
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import error  # This is needed for error handling like telegram.error.TimedOut
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from asgiref.sync import sync_to_async
import re
import time
import qrcode
from io import BytesIO
import asyncio
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
            [
                InlineKeyboardButton("➕ Add Product", callback_data="add_product"),  # Frequently used actions together
                InlineKeyboardButton("✏️ Edit Product", callback_data='edit_product')
            ],
            [
                InlineKeyboardButton("❌ Delete Product", callback_data='delete_product')  # Isolated action
            ],
            [
                InlineKeyboardButton("🗑️ Delete Category", callback_data="delete_category"),  # Actions related to categories together
                InlineKeyboardButton("🛠️ Edit Store Info", callback_data="edit_store_info")
            ],
            [
                InlineKeyboardButton("🌐 Get Website & QR Code", callback_data="get_website_qr")  # Isolated utility action
            ]
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
    if update.message:
        await update.message.reply_text('Please send the username for the account.')
        context.user_data['state'] = 'awaiting_username'
    elif update.callback_query:
        await update.callback_query.message.reply_text('Please send the username for the account.')
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
    elif user_state == 'awaiting_new_name':
        await update_product_name(update, context)
    elif user_state == 'awaiting_new_price':
        await update_product_price(update, context)
    elif user_state =="awaiting_title_update":
        await handle_title_update(update, context)
    elif user_state == 'awaiting_new_image':
        await update_product_image(update, context)
    else:
        await start(update, context)

async def edit_store_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()  # Acknowledge the callback
    keyboard = [
        [InlineKeyboardButton("Edit Logo", callback_data="edit_logo")],
        [InlineKeyboardButton("Edit Title", callback_data="edit_title")],
        [InlineKeyboardButton("Edit Color", callback_data="edit_color")],
        [InlineKeyboardButton("Cancel", callback_data="cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.reply_text(
        "What would you like to edit?",
        reply_markup=reply_markup
    )

async def edit_logo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = 'awaiting_edit_logo'
    await update.callback_query.answer()  # Acknowledge the callback
    # Set the state to indicate the user is uploading a new logo
    print("context.user_data['state'] ")
    print(context.user_data['state'] )
    await update.callback_query.message.reply_text("Please upload the new logo image.")

async def handle_edit_logo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Ensure that the user uploaded a photo
        if not update.message.photo:
            await update.message.reply_text('Please upload an image of the logo.')
            return

        # Get the file from the uploaded photo
        logo_file = await update.message.photo[-1].get_file()

        # Define a path to save the new logo
        logo_path = f"static/img/logos/{context.user_data['chat_id']}_logo_{int(time.time())}.jpg"

        # Download the image to the server
        await logo_file.download_to_drive(logo_path)

        # Get the user's account from the cached data
        account = context.user_data['account']

        # Update the account's logo
        account.logo = logo_path
        await sync_to_async(account.save)()

        # Confirm the update
        await update.message.reply_text("Your logo has been updated successfully! 🎉")
        
        # Clear the user state after the logo has been updated
        context.user_data['state'] = None

    except Exception as e:
        await update.message.reply_text(f"An error occurred while updating the logo: {str(e)}")


async def handle_title_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_title = update.message.text

        # Update the Account's title field
        account = context.user_data['account']
        account.title = new_title
        await sync_to_async(account.save)()

        # Confirm the update to the user
        await update.message.reply_text(f"✅ Your title has been updated to '{new_title}' successfully!")

        # Clear the user state
        context.user_data['state'] = None

    except Exception as e:
        await update.message.reply_text(f"An error occurred while updating the title: {str(e)}")



async def update_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product = context.user_data.get('product')
    new_name = update.message.text
    product.item = new_name
    await sync_to_async(product.save)()

    await update.message.reply_text(f"Product name updated to: {product.item}")
    context.user_data.pop('product')
    context.user_data.pop('state')

async def update_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product = context.user_data.get('product')
    new_price = update.message.text
    product.price = new_price
    await sync_to_async(product.save)()

    await update.message.reply_text(f"Product price updated to: {product.price}")
    context.user_data.pop('product')
    context.user_data.pop('state')

async def update_product_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Assuming you handle image uploads differently, adjust this function accordingly
    product = context.user_data.get('product')
    new_image = update.message.photo[-1].file_id  # Example of how to get image (Telegram file ID)
    product.image = new_image
    await sync_to_async(product.save)()

    await update.message.reply_text("Product image updated successfully.")
    context.user_data.pop('product')
    context.user_data.pop('state')




# Handle account username step
async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text
    context.user_data['username'] = username
    await update.message.reply_text('Now please send the logo (as an image) for the Store.')
    context.user_data['state'] = 'awaiting_logo'

# Handle account logo step
async def handle_logo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the upload is an image
    await update.message.reply_text('Downloading your logo, this may take a few moments...')

    chat_id = context.user_data.get('chat_id', update.message.chat.id)
    context.user_data['chat_id'] = chat_id  # Cache chat ID

    try:
        # Get the highest resolution photo (last one in the list)
        logo_file = await update.message.photo[-1].get_file()

        # Get file metadata to ensure it's an image (Telegram will provide only valid image files in update.message.photo)
        if logo_file.file_path.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            logo_path = f"static/img/logos/{chat_id}_logo.jpg"
            await logo_file.download_to_drive(logo_path)

            # Confirm successful download and update state
            await update.message.reply_text('Logo downloaded successfully.')
            context.user_data['logo'] = logo_path
            await update.message.reply_text('Now please send the title for the Store.')
            context.user_data['state'] = 'awaiting_title'
        else:
            await update.message.reply_text('The file uploaded is not a valid image format. Please upload a .jpg, .jpeg, .png, or .gif file.')

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
            InlineKeyboardButton("Cancel", callback_data="cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Category '{category_name}' does not exist for this account. Do you want to create it?",
        reply_markup=reply_markup
    )


async def show_categories_for_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.callback_query.message.chat.id
    account = context.user_data.get('account')

    if not account:
        # Try to retrieve the account again in case it's not in user_data
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.callback_query.message.reply_text("No account found. Please add an account first.")
            return

    # Fetch categories related to the account asynchronously
    categories = await sync_to_async(list)(Category.objects.filter(account=account))  # Ensure it's a list

    if not categories:
        await update.callback_query.message.reply_text("No categories available to delete.")
        return

    # Create InlineKeyboard with category names as options
    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(category.name, callback_data=f"delete_category_{category.id}")])

    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])  # Add a cancel button
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(
        "Select the category you want to delete:",
        reply_markup=reply_markup
    )


async def delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    category_id = query.data.split("_")[2]  # Extract the category ID from the callback data

    try:
        category = await sync_to_async(Category.objects.get)(id=category_id)
        await sync_to_async(category.delete)()  # Delete the category

        await query.message.reply_text(f"Category '{category.name}' has been deleted successfully.")
    except Exception as e:
        await query.message.reply_text(f"An error occurred while deleting the category: {str(e)}")

# Handle item name step
async def handle_item_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    item_name = update.message.text
    context.user_data['item_name'] = item_name
    await update.message.reply_text('Please provide the price for the product.')
    context.user_data['state'] = 'awaiting_price'


async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE):

    price = update.message.text

    if not price.isdigit():
        await update.message.reply_text("Invalid price. Please enter a numeric value.")
        return

    context.user_data['price'] = int(price)
    await update.message.reply_text('Please provide a description for the product.')
    context.user_data['state'] = 'awaiting_description'

async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text
    context.user_data['description'] = description  # Store the description for the next step
    await update.message.reply_text('Please send an image of the product.')
    context.user_data['state'] = 'awaiting_image'

async def handle_product_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
  
    await update.message.reply_text('Downloading your product image, this may take a few moments...')

    try:
        # Download the product image
        product_image_file = await update.message.photo[-1].get_file()
        product_image_path = f"static/img/items/{context.user_data['chat_id']}_product_{int(time.time())}.jpg"
        await product_image_file.download_to_drive(product_image_path)
        await update.message.reply_text('Product image downloaded successfully.')

        # Save the menu item with all the information
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

        # Get the website URL for the account
        username = account.username  # Get the username from the cached account
        website_url = f"https://tidytaps-r92c.vercel.app/f/{username}"

        # Generate the QR code for the website URL
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(website_url)
        qr.make(fit=True)

        # Save the QR code image in memory
        qr_img = qr.make_image(fill='black', back_color='white')
        qr_bytes = BytesIO()
        qr_img.save(qr_bytes, format='PNG')
        qr_bytes.seek(0)

        # Send the success message with the website link
        await update.message.reply_text(
            f"🎉 Product '{menu_item.item}' added successfully! You can add another product by typing /add_product.\n"
            f"Visit your product page at: {website_url}"
        )
        await update.message.reply_photo(photo=qr_bytes, caption=f"Scan the QR code to visit your website page: {website_url}")

        context.user_data.clear()

    except Exception as e:
        print(e)
        await update.message.reply_text(f'An error occurred while downloading the product image: {str(e)}')


async def show_products_for_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        account = context.user_data.get('account')

        # Fetch products related to the account using sync_to_async for Django ORM query
        products = await sync_to_async(list)(MenuItem.objects.filter(account=account))

        if not products:
            await update.callback_query.message.reply_text("No products available to delete.")
            return

        # Create InlineKeyboard with product names as options
        keyboard = []
        for product in products:
            keyboard.append([InlineKeyboardButton(product.item, callback_data=f"delete_product_{product.id}")])

        keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.message.reply_text(
            "Select the product you want to delete:",
            reply_markup=reply_markup
        )

    except Exception as e:
        await update.callback_query.message.reply_text(f"An error occurred: {str(e)}")

async def delete_selected_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    product_id = query.split("_")[-1]  # Extract the product ID from the callback data

    try:
        # Fetch and delete the selected product
        product = await sync_to_async(MenuItem.objects.get)(id=product_id)
        await sync_to_async(product.delete)()

        await update.callback_query.message.reply_text(f"Product '{product.item}' has been deleted successfully!")

    except MenuItem.DoesNotExist:
        await update.callback_query.message.reply_text("The selected product does not exist.")
    except Exception as e:
        await update.callback_query.message.reply_text(f"An error occurred: {str(e)}")


async def handle_image_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        if update.message.video:
            await update.message.reply_text('You uploaded a video. Please upload an image instead.')
            return
        elif update.message.document:
            await update.message.reply_text('You uploaded a document. Please upload an image instead.')
            return
        else:
            await update.message.reply_text('Please upload an image.')
            return

    # Check the state and handle accordingly
    print(context.user_data.get('state'))
    if context.user_data.get('state') == 'awaiting_logo':
        await handle_logo(update, context)
    elif context.user_data.get('state') == 'awaiting_product_image' or context.user_data.get('state') == "awaiting_image" :
        await handle_product_image(update, context)
    elif context.user_data.get('state') == "awaiting_new_image":
        await update_product_image(update, context)

    elif context.user_data.get('state') == "awaiting_edit_logo":
        await handle_edit_logo(update, context)
    else:
        await update.message.reply_text('Please Read the message Again.')


async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.callback_query.message.chat.id
    # Assuming context.user_data['account'] has the logged-in account details
    account = context.user_data.get('account')

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account  # Cache the account in user_data
        except Account.DoesNotExist:
            keyboard = [
                [InlineKeyboardButton("Add Account", callback_data="add_account")],
                [InlineKeyboardButton("Cancel", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.message.reply_text(
                "No account found associated with your Telegram ID. Please create an account first.",
                reply_markup=reply_markup
            )
            return

    # Fetch the products for the account using sync_to_async to avoid the synchronous operation error
    products = await sync_to_async(list)(MenuItem.objects.filter(account=account))  # Ensure it's converted to a list

    if not products:
        await update.callback_query.message.reply_text("No products found for editing.")
        return

    # Create inline buttons for each product
    keyboard = []
    for product in products:
        keyboard.append([InlineKeyboardButton(product.item, callback_data=f"edit_{product.id}")])

    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Since this is triggered from a button, you need to use callback_query.message
    await update.callback_query.message.reply_text("Choose a product to edit:", reply_markup=reply_markup)



async def edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id):
    # Fetch the selected product by ID
    try:
        product = await sync_to_async(MenuItem.objects.get)(id=product_id)
        context.user_data['product'] = product  # Cache the product in user_data

        # Show buttons for editing options: Name, Price, Image
        keyboard = [
            [InlineKeyboardButton("Edit Name", callback_data=f"edit_name_{product.id}")],
            [InlineKeyboardButton("Edit Price", callback_data=f"edit_price_{product.id}")],
            [InlineKeyboardButton("Edit Image", callback_data=f"edit_image_{product.id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.message.reply_text(
            f"You selected: {product.item}\nChoose what you want to edit:",
            reply_markup=reply_markup
        )

    except MenuItem.DoesNotExist:
        await update.callback_query.message.reply_text("The selected product does not exist.")


async def send_website_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        account = context.user_data.get('account')
        if not account:
            await update.callback_query.message.reply_text("No account found.")
            return

        # Generate the website URL
        username = account.username
        website_url = f"https://tidytaps-r92c.vercel.app/f/{username}"

        # Generate the QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(website_url)
        qr.make(fit=True)

        # Save the QR code image in memory
        qr_img = qr.make_image(fill='black', back_color='white')
        qr_bytes = BytesIO()
        qr_img.save(qr_bytes, format='PNG')
        qr_bytes.seek(0)

        # Send the website URL and QR code
        await update.callback_query.message.reply_text(f"Your website URL is: {website_url}")
        await update.callback_query.message.reply_photo(photo=qr_bytes, caption="Here is your QR code.")
    
    except Exception as e:
        await update.callback_query.message.reply_text(f"An error occurred: {str(e)}")


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handle video upload scenario
    if context.user_data.get('state') == "awaiting_logo":
        await update.message.reply_text('You uploaded a video for the logo. Please upload an image as the logo for the Store.')

    elif context.user_data.get('state') == "awaiting_product_image":
        await update.message.reply_text('You uploaded a video for the product image. Please upload an image for the product instead.')
    else:
        await update.message.reply_text('You uploaded a video. Please upload an image instead if you intended to upload a logo or product image.')


async def handle_product_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product = context.user_data.get('product')
    
    # Example: handle updating the product name (similarly handle other fields)
    product.item = update.message.text
    await sync_to_async(product.save)()

    await update.message.reply_text(f"Product '{product.item}' updated successfully.")
    context.user_data.pop('product')  # Clear product from context after update

async def start_editing_name(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id):
    product = context.user_data.get('product')
    if product and product.id == product_id:
        await update.callback_query.message.reply_text("Please send the new name for the product.")
        context.user_data['state'] = 'awaiting_new_name'
    else:
        await update.callback_query.message.reply_text("Product not found.")

async def start_editing_price(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id):
    product = context.user_data.get('product')
    if product and product.id == product_id:
        await update.callback_query.message.reply_text("Please send the new price for the product.")
        context.user_data['state'] = 'awaiting_new_price'
    else:
        await update.callback_query.message.reply_text("Product not found.")

async def edit_image_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    # Extract the product ID from the callback data
    _, product_id = query.data.split('_')
    context.user_data['editing_product_id'] = int(product_id)  # Store the product ID in user data

    await query.edit_message_text(text="Please upload the new image for the product.")


async def start_editing_image(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id):
    try:
        
        await update.callback_query.message.reply_text('Please upload an image of the product.')
        context.user_data['state'] = 'awaiting_new_image'

    except Exception as e:
        print(e)
        await update.callback_query.message.reply_text(f'An error occurred while downloading the product image: {str(e)}')


async def edit_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()  # Acknowledge the callback
    context.user_data['state'] = 'awaiting_title_update'
    await update.callback_query.message.reply_text('Please enter the new title for your store.')

async def cancel_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()  # Clear the current state and any cached data
    await update.message.reply_text("Process has been canceled. You can start again by using /start.")

# Handle button clicks
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "add_account":
        await add_account(update, context)

    elif query.data == "add_product":
        await add_product(update, context)

    elif query.data == 'edit_product':
        await query.message.reply_text('Please choose a product to edit.')
        await show_products(update, context)

    elif query.data == "cancel":
        context.user_data.clear()
        await query.message.reply_text("Process has been canceled. You can start again by using /start.")
        return
    elif query.data.startswith("edit_name_"):
        product_id = int(query.data.split("_")[2])  # Extract the product ID
        await start_editing_name(update, context, product_id)

    elif query.data.startswith("edit_price_"):
        product_id = int(query.data.split("_")[2])  # Extract the product ID
        await start_editing_price(update, context, product_id)

    elif query.data.startswith("edit_image_"):
        product_id = int(query.data.split("_")[2])  # Extract the product ID
        await start_editing_image(update, context, product_id)

    elif query.data.startswith("edit_store_info"):
        await edit_store_info(update, context)

    elif query.data == "delete_category":
        await show_categories_for_deletion(update, context)  # Call the function to show categories for deletion

    elif query.data == "get_website_qr":  # New handler for the QR code
        await send_website_qr(update, context)
        
    elif query.data.startswith("delete_category_"):
        await delete_category(update, context)

    elif query.data.startswith("edit_logo"):
        await edit_logo(update, context)

    elif query.data.startswith("edit_title"):
        await edit_title(update, context)

    elif query.data == 'delete_product':
        await query.message.reply_text('Please choose a product to edit.')
        await show_products_for_deletion(update, context)

    elif query.data.startswith('delete_product_'):
        await delete_selected_product(update, context)

    elif query.data.startswith("edit_"):
        product_id = int(query.data.split("_")[1])  # Extract the product ID from the callback data
        await edit_product(update, context, product_id)

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
    else:
        print(query.data)
        print("nothinngg")



# Main function to start the bot
if __name__ == '__main__':
    token = "6977293897:AAE9OYhwEn75eI6mYyg9dK1_YY3hCB2M2T8"  # Replace with your bot token
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(CommandHandler("add_account", add_account))
    application.add_handler(CommandHandler("add_product", add_product))
    application.add_handler(CommandHandler("edit_product", show_products))
    application.add_handler(CommandHandler("cancel", cancel_process))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image_upload))  # Expecting a logo first

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_click))
    print("Telegram Bot Started !!")
    application.run_polling()
