# Import necessary libraries and modules
import json
import os
import sys
import django
from django.db import IntegrityError  # Import IntegrityError
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile, KeyboardButton, WebAppInfo
from telegram import error  # This is needed for error handling like telegram.error.TimedOut
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from asgiref.sync import sync_to_async
import re
import time
import qrcode
from io import BytesIO
import asyncio
from urllib.parse import quote
from telegram.constants import ChatAction
from telegram.ext import CallbackContext
from PIL import Image
import io
import requests
from urllib.parse import quote
from telegram.ext import ConversationHandler



# Add the project root to sys.path so Python can find 'tidytap'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tidytap.settings')
django.setup()

# Now you can import your models
from accounts.models import Account, MenuItem, Category, Delivery,MenuItemPhoto , Contacts, Adresses, SocialMedia, Option, MenuItemChoices, Cover,CouponCode
from django.contrib.auth.models import User

LANGUAGES = {
    'en': 'English',
    'ar': 'العربية'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("start")
    args = context.args
    if args:
        # Get the first parameter (e.g., SudanPromoter)
        parameter = args[0]
        print(parameter)
        context.user_data["promoter"] = str(parameter)
        
    # Send a message asking the user to choose a language
    keyboard = [
        [InlineKeyboardButton(LANGUAGES['en'], callback_data='lang_en')],
        [InlineKeyboardButton(LANGUAGES['ar'], callback_data='lang_ar')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please choose your language / يرجى اختيار لغتك", reply_markup=reply_markup)

async def show_start_message(update: Update, context: ContextTypes.DEFAULT_TYPE, account):
    # Fetch the selected language
    selected_lang = account.language

    # Use the get_message function to fetch the appropriate text
    welcome_message = get_message(account, 'welcome_back').format(username=account.username)
    commands_message = get_message(account, 'commands')

    # Buttons with translations
    buttons = MESSAGES[selected_lang]['buttons']
    keyboard = [
        [
            InlineKeyboardButton(buttons['add_product'], callback_data="add_product"),
            InlineKeyboardButton(buttons['edit_product'], callback_data='edit_product')
        ],
        [
            InlineKeyboardButton(buttons['delete_product'], callback_data='delete_product')
        ],
        [
            #InlineKeyboardButton(buttons['delete_category'], callback_data="delete_category"),
            InlineKeyboardButton(buttons['edit_category'], callback_data="edit_category_menu"),
            InlineKeyboardButton(buttons['edit_store_info'], callback_data="edit_store_info")
        ],
        [
            # "See Orders" button with conditional logic for subscription plan
            InlineKeyboardButton(
                buttons['see_orders'],
                callback_data="upgrade_plan" if account.subscription_plan == "free" else None,
                web_app=WebAppInfo(url=f"https://www.tidy-taps.com/orders/{account.id}")
                if account.subscription_plan != "free" else None
            )
        ],
        [
            InlineKeyboardButton(buttons['edit_style'], callback_data="edit_style")  # New Style button
        ],
        [
            InlineKeyboardButton(buttons['get_analytics'], callback_data="get_analytics") 
        ],
        [
            InlineKeyboardButton(buttons['get_website_qr'], callback_data="get_website_qr")
        ],
        [
            InlineKeyboardButton(buttons['help'], callback_data="help")  # New Help button
        ],
        [
            InlineKeyboardButton(buttons['settings'], callback_data="settings")  # Settings button added
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Check if the message comes from a callback query or a regular message
    if update.callback_query:
        await update.callback_query.message.reply_text(
            welcome_message + commands_message, 
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            welcome_message + commands_message, 
            reply_markup=reply_markup
        )




MESSAGES = {
    'en': {
        'welcome_back': "Welcome back, {username}! 🎉\n\n",
        'welcome_new': "Welcome to the bot! 🎉\n\n",
        'commands': "You can use the following commands:",
        'no_account': "You need to create an account first",
        'provide_category': "Please provide the category for the product.",
        'unable_to_determine_chat_id': "Unable to determine chat ID.",
        'category_confirmation': "Category '{category_name}' does not exist for this account. Do you want to create it?",
        'category_creation_success': "Category '{category_name}' created successfully! Please provide the product name to add it, or press cancel.",
        'item_name_prompt': "Please provide the item name.",
        'item_price_prompt': "Please provide the price for the product.",
        'invalid_price': "Invalid price. Please enter a numeric value.",
        'awaiting_description': "Please provide a description for the product.",
        'awaiting_image': "Please send an image of the product.",
        'create_account_first': "You need to create an account first",
        'no_products_available': "No products available to delete.",
        'no_products': "No products available.",
        'select_product_to_delete': "Select the product you want to delete:",
        'cancel': "Cancel",
        'error_occurred': "An error occurred: {error}",
        'get_website_qr': "🌐 Get Website & QR Code",
        'image_download_error': 'An error occurred while downloading the product image: {error}',
        'add_product': "➕ Add Product",
        'edit_product': "✏️ Edit Product",
        'delete_product': "❌ Delete Product",
        'delete_category': "🗑️ Delete Category",
        'edit_store_info': "🛠️ Edit Store Info",
        'downloading_image': "Downloading your product image, this may take a few moments...",
        'image_downloaded_successfully': "Product image downloaded successfully.",
        'product_added_successfully': "🎉 Product '{item}' added successfully!",
        'visit_product_page': "Visit your product page at: {url}",
        'control_over_all_things': "Control Over All Things! 🎉\n\n",
        'product_deleted': "Product '{product_name}' has been deleted successfully!",
        'product_not_exist': "The selected product does not exist.",
        'video_upload': "You uploaded a video. Please upload an image instead.",
        'document_upload': "You uploaded a document. Please upload an image instead.",
        'no_image_upload': "Please upload an image.",
        'read_message_again': "Please read the message again.",
        'no_account_found': "No account found. Please add an account first.",
        'add_account': "Add Account",
        'website_url': "Your website URL is: {website_url}",
        'qr_code_caption': "Here is your QR code.",
        'no_categories_available': "No categories available to delete.",
        'select_category_to_delete': "Select the category you want to delete:",
        'edit_name': "Edit Name",
        'edit_price': "Edit Price",
        'edit_image': "Edit Image",
        'selected_product': "You selected: {}. Choose what you want to edit:",
        'video_for_logo': 'You uploaded a video for the logo. Please upload an image as the logo for the Store.',
        'video_for_product_image': 'You uploaded a video for the product image. Please upload an image for the product instead.',
        'general_video_upload': 'You uploaded a video. Please upload an image instead if you intended to upload a logo or product image.',
        'product_update_success': "Product '{0}' updated successfully.",
        'edit_product_name': "Please send the new name for the product.",
        'edit_product_price': "Please send the new price for the product.",
        'edit_product_image': "Please upload the new image for the product.",
        'upload_product_image': "Please upload an image of the product.",
        'product_not_found': "Product not found.",
        'error_message': "An error occurred: {0}",
        'enter_new_title': "Please enter the new title for your store.",
        'process_canceled': "Process has been canceled. You can start again by using /start.",
        'price_updated': "Product price updated to: {new_price}",
        'edit_logo': "Edit Logo",
        'edit_title': "Edit Title",
        'edit_color': "Edit Color",
        'edit_primary_color': "Edit Primary Color",
        'edit_secondary_color': "Edit Secondary Color",
        'which_color_to_edit': "Which color would you like to edit?",
        'send_primary_color': "Please send the new primary color in hex format (e.g., #0E214B).",
        'send_secondary_color': "Please send the new secondary color in hex format (e.g., #3F68DE).",
        'invalid_hex_format': "Invalid hex format! Please send the color in hex format (e.g., #0E214B).",
        'account_not_found': "No account found. Please create an account first using /add_account.",
        'primary_color_updated': "✅ Your primary color has been updated to {new_color} successfully!",
        'secondary_color_updated': "✅ Your secondary color has been updated to {new_color} successfully!",
        'upload_logo': "Please upload the new logo image.",
        'upload_logo_image': "Please upload an image of the logo.",
        'logo_updated': "Your logo has been updated successfully! 🎉",
        'error_updating_logo': "An error occurred while updating the logo",
        'title_updated': "✅ Your title has been updated to '{new_title}' successfully!",
        'edit_delivery_fees': 'Edit Delivery Fees',
        'error_updating_title': "An error occurred while updating the title",
        'product_name_updated': "Product name updated to: {new_name}",
        'product_image_updated': "Product image updated successfully.",
        'enter_new_category': "Please enter the name of the new category:",
        'product_not_found': "Product not found.",
        'what_to_edit': 'What would you like to edit?',
        'category_deleted': "Category '{category_name}' has been deleted successfully.",
        'category_delete_error': "An error occurred while deleting the category: {error_message}",
        'send_username': 'Please send the **username** for your store.\n\n'
                         'This username will be part of your store\'s website URL, like this:\n'
                          '👉 tidy-taps.c*m/s/your-username\n\n',
        'send_logo': 'Now please send the **logo** (as an image) for the store.',
        'downloading_logo': 'Downloading your logo, this may take a few moments...',
        'logo_downloaded': 'Logo downloaded successfully.',
        'ask_title': 'Now please send the **title** for the Store.',
        'invalid_image_format': 'The file uploaded is not a valid image format. Please upload a .jpg, .jpeg, .png, or .gif file.',
        'error_downloading_logo': 'An error occurred while downloading the logo: {}',
        'ask_phone_number': 'Finally, please send the WhatsApp phone number for the account.',
        'invalid_phone_number': 'Invalid phone number. Please enter a valid phone number. For Egypt, use 01XXXXXXXXX, and for Morocco, use +212XXXXXXXXX or 0XXXXXXXXX.',
        'user_not_found': 'User with ID 1 does not exist.',
        'account_added_success': '🎉 Account added successfully!\n\nYou can now add a new product for your account by clicking the "Add Product" button below. Follow the prompts to specify the product category, name, price, description, and image.',
        'welcome_message': 'You can control everything! 🎉\n\n',
        'commands_prompt': 'You can use the following commands:',
        'username_taken': 'The username you provided is already taken. Please choose a different username and try again.',
        'create_new_category': 'Create New Category',
        'help': "For further assistance, contact us on WhatsApp: \n wa.me/+201554516636",
        'photo_required': "Please send the LOGO photo, not text or any other file type.",
        'ask_delivery_fee': 'Would you like to set delivery fees for your store?',
        'enter_delivery_fee': 'Please enter the delivery fee amount:',
        'delivery_fee_set': 'Delivery fee set to: {}',
        'invalid_delivery_fee': 'Invalid input. Please enter a valid number for the delivery fee.',
        'no_delivery_fee_set': 'No delivery fee has been set.',
        'invalid_image_type': 'Please upload a valid image.',
        'ask_upload_another_photo': 'Do you want to upload another photo?',
        'no_more_photos': 'No more photos to upload.',
        'edit_contacts': "Edit Contacts",  # New entry for editing contacts
        'edit_addresses': "Edit Addresses",  # New entry for editing addresses
        'edit_social_media': "Edit Social Media",
        'choose_contact_to_edit_or_create': 'Choose a contact to edit or create a new one:',
        'create_new_contact': '➕ Create New Contact',
        'select_contact': "Please select a contact to edit or create a new one:",
        'enter_new_contacts': "Please enter the phone number for the new contact:",
        'contact_added': "Contact phone number has been successfully added.",
        'invalid_phone': "Please enter a valid phone number.",
        'edit_contact_phone': "Please enter the new phone number for this contact:",
        'contact_not_found': "The selected contact was not found.",
        'contact_updated': "Contact details have been updated.",
        'select_contact_to_delete': "Please select a contact to delete:",
        'confirm_contact_delete': "Are you sure you want to delete this contact?",
        'contact_deleted': "The contact has been deleted successfully.",
        'confirm': "Yes, Delete",
        'delete_contact': "Delete a Contact",
        'select_action': "Please select an action:",
        'enter_new_address': "Please provide the details for the new address:",
        'edit_addresses': "Edit Addresses",
        'create_new_address': "Create New Address",
        'select_address': "Select an address to edit or create a new one:",
        'editing_address': "Editing address",
        'address_added': "The address has been added successfully.",
        'address_updated': "The address has been updated successfully.",
        'address_deleted': 'The address has been deleted successfully.',
        'address_not_found': 'The address you are trying to delete does not exist.',
        'operation_cancelled': 'Operation cancelled.',
        'select_address_to_delete': 'Please select an address to delete:',
        'delete_address': 'Delete Address',
        'edit_social_media': 'Edit Social Media',
        'select_social_media': 'Select a social media platform to edit:',
        'edit_facebook': 'Edit Facebook Link',
        'edit_instagram': 'Edit Instagram Link',
        'edit_whatsapp': 'Edit WhatsApp Link',
        'edit_tiktok': 'Edit TikTok Link',
        'enter_facebook_link': 'Please enter your Facebook link:',
        'enter_instagram_link': 'Please enter your Instagram link:',
        'enter_whatsapp_link': 'Please enter your WhatsApp link:',
        'enter_tiktok_link': 'Please enter your TikTok link:',
        'social_media_updated': 'Social media link updated successfully!',
        'no_social_media': 'No social media links found. Please add them first.',
        'invalid_instagram_link': 'Please enter a valid Instagram link starting with "instagram.com", "https://www.instagram.com/", or "www.instagram.com".',
        'social_media_instagram_updated': 'Instagram link updated successfully.',
        'invalid_whatsapp_link': 'Please enter a valid WhatsApp link starting with "wa.me/".',
        'social_media_whatsapp_updated': 'WhatsApp link updated successfully.',
        'invalid_tiktok_link': 'Please enter a valid TikTok link starting with "tiktok.com".',
        'social_media_tiktok_updated': 'TikTok link updated successfully.',
        'invalid_facebook_link': 'Please enter a valid Facebook link starting with "facebook.com".',
        'social_media_facebook_updated': 'Facebook link updated successfully.',
        'do_you_want_to_add_options': "❓ Would you like to add options for this product? 🛍️",
        'provide_option_title': "🏷️ Please provide a title for this option (e.g., Size, Color):",
        'provide_option_values': "Now, please enter the values for this option (e.g., Small, Medium, Large), separated by commas:",
        'option_added_successfully': "Option added successfully!",
        'add_more_options': "Would you like to add more options for this product?",
        'provide_single_option_value': "🔢 Please enter a value for this option (e.g., Small, Red):",
        'provide_single_option_price': "💰 Now, please enter the price for '{value}' (this will be added to the product price. Enter 0 if there’s no additional cost):",
        'add_more_option_values': "Would you like to add another value for this option? Please enter it, or type 'done' to finish:",
        'options_completed': "✅ You have completed adding options.",
        'options_completed': "✅ You have completed adding options.",
        'add_another_option_title': "➕ Would you like to add another option title?",
        'edit_option': "Edit Options",
        'choose_option_to_edit': "Choose an option to edit:",
        'edit_option_title': "Edit Option Title",
        'edit_option_choices': "Edit Option Choices",
        'enter_new_option_title': "Enter the new title for the option:",
        'option_title_updated': "The option title has been updated to: {0}",
        'enter_new_choice_value': "Enter the new value for this choice:",
        'choice_value_updated': "The choice value has been updated to: {0}",
        'choose_choice_to_edit_or_add': "Choose a choice to edit, or add a new one:",
        'add_new_choice': "Add New Choice",
        'option_not_exist': "This option doesn't exist.",
        'no_options_to_edit': "No options available for this product.",
        'choice_not_exist': "This choice doesn't exist.",
        'edit_option_prompt': "You are editing option: {0}. What would you like to do?",
        'edit_choice_value': "Edit Value",  # Button label for editing the choice name/value
        'edit_choice_price': "Edit Price",  # Button label for editing the choice price
        'choose_edit_action': "What would you like to edit for '{0}'?",  # Message asking what to edit, where {0} is the choice name
        'choice_price_updated': "The choice price has been updated to '{0}'.",  # Message confirming the price change
        'enter_new_price': "💰 Please enter the new price for '{0}' (enter 0 if there is no additional price):",
        'invalid_price': "Invalid input! Please enter a valid price.",
        'enter_new_choice_name': "Please enter the name for the new choice:",
        'enter_new_choice_price': "Please enter the price for the new choice (enter 0 if there is no additional cost):",
        'new_choice_added': "New choice '{0}' with price {1} has been added successfully.",
        'enter_option_name': "📋 Please enter the name of the new option (e.g., Color, Size):",
        'enter_choice_name': "🏷️ Please enter the name of the choice (e.g., Red, Blue):",  # Replaced the palette icon with a tag icon
        'enter_choice_price': "💰 Please enter the price for this choice:",
        'add_another_choice_prompt': "➕ Do you want to add another choice?",
        'add_new_option': "➕ Add New Option",
        'finished_adding_choices': "✅ You have finished adding choices for this option.",
        'remove_option': "❌ Remove Option",
        'confirm_remove_option': "⚠️ Are you sure you want to remove the option '{}'? This action cannot be undone.",
        'option_removed': "✅ Option removed successfully.",
        'removal_canceled': "❌ Option removal canceled.",
        'edit_whatsapp_number': "Edit WhatsApp Number",
        'enter_new_phone_number': "Please enter your new phone number:",
        'whatsapp_number_updated': "Your WhatsApp number has been updated successfully.",
        'invalid_phone_number': "The phone number you entered is invalid. Please ensure it starts with '+' followed by the country code (e.g., +1 for USA, +44 for UK) and contains only numbers.",
        'enter_new_description': "Please enter the new description for the product:",
        'description_updated': "Product description updated successfully.",
        'edit_description': "Edit Description",
        'too_many_images': "You can only upload up to {max_images} images. Please try again with fewer images.",
        'upload_cover_instruction': "Please upload a cover photo for your store. This will appear at the top of your website.",
        'cover_uploaded_successfully': "Cover photo uploaded successfully!",
        'upload_another_cover': "Would you like to upload another cover photo?",
        'upload_cover_instruction': "Please upload another cover photo for your store.",
        'cover_upload_complete': "Cover upload completed. Thank you!",
        'ask_upload_another_cover': "Would you like to upload another cover image?",
        'downloading_image': "Downloading the image...",
        'cover_downloaded_successfully': "Cover image uploaded successfully!",
        'cover_download_error': "An error occurred while downloading the cover image: {error}",
        'invalid_image_type': "Please send a valid image file.",
        'upload_error': "There was an error uploading your cover photo. Please try again.",
        "upload_another_cover_inst":"Please Upload another cover photo",
        'choose_cover_action': "Would you like to add a new cover or delete an existing one?",
        'upload_cover_instruction': "Please upload a new cover image.",
        'cover_deleted': "The cover image has been deleted.",
        'cover_not_found': "No cover found to delete.",
        'choose_delivery_option': "Choose an option for delivery fees:",
        'enter_delivery_details': "Please enter the city for the new delivery fee.",
        'choose_delivery_to_edit': "Select a delivery entry to edit.",
        'choose_delivery_to_delete': "Select a delivery entry to delete.",
        'delivery_added': 'Delivery to %s has been added with a fee of %s.',
        'delivery_deleted': "Delivery for city %s has been deleted.",
        'add_delivery': "Add Delivery",
        'delete_delivery': "Delete Delivery",
        'add_image': "➕ Add Image",
        'remove_image': "❌ Remove Image",
        'choose_image_action': "Please choose an action for the product image:",
        'choose_image_to_remove': "Please select an image to remove:",
        'no_images_to_remove': "No images available to remove.",
        'image_removed_success': "Image has been successfully removed.",
        'image_added_success': "The image has been successfully added to the product!",
         "get_analytics": (
            "📊 *Analytics for Account*\n"
            "Total Views: {total_views}\n"
            "Total Visits: {total_visits}\n"
        ),
        "loading_message": "Loading analytics data... Please wait.",
        "failed_fetch": "Failed to fetch analytics. Status code: {status_code}",
        'edit_cover': "Edit Cover",
        'choose_category_action': "Choose a category action:",
        'choose_category_to_edit': "Choose a category to edit:",
        'enter_new_category_name': "Please enter the new name for the category:",
        'category_updated_successfully': "The category has been updated successfully.",
        'category_not_found': "The selected category could not be found.",
        'confirm_delete_message': "Are you sure you want to delete this category?",
        'edit_offer': "Edit Offer",
        'enter_offer': "The current price of *{product_name}* is {product_price}.\nPlease enter the new offer details for this product:",
         'invalid_offer': "The offer value must be a valid number. Please try again.",
        'offer_updated': "The offer for *{product_name}* has been successfully updated to {new_offer}.",
        'error_occurred': "An error occurred while updating the offer. Please try again later.",
        'unrecognized_message': "I didn't understand that. Please use the available options.",
        'edit_currency': "Change Currency",
        'select_currency': "Please select a currency:",
        'currency_selected': "You have selected currency:",
        'previous': "⬅️ Previous",
        'next': "Next ➡️",
        'currency_updated': "Your currency has been updated to: {currency}.",
        'upload_new_category_picture': "Please upload the new category picture.",
        'category_picture_updated': "The category picture has been updated successfully!",
        'invalid_picture_format': "Invalid format. Please upload a valid picture.",
        'no_category_selected': "No category has been selected for editing.",
        'downloading_category_image': "Downloading the category image, please wait...",
        'category_image_downloaded_successfully': "The category image has been downloaded successfully!",
        "edit_coupons": "Discound Coupons",
        "ask_for_edit_coupons":"What would you like to do with coupons?",
        'enter_coupon_code': "Please enter the coupon code:",
        'enter_coupon_amount': "Please enter the coupon amount:",
        'invalid_amount': "Invalid amount. Please enter a valid number.",
        'coupon_added': "Coupon added successfully! 🎉",
        'select_coupon_to_remove': "Select the coupon you want to remove:",
        'coupon_removed': "Coupon removed successfully! 🗑️",
        'coupon_not_found': "Coupon not found. It might have already been removed.",
        'no_coupons': "No coupons available to remove.",
        "Add_Coupon" : "➕ Add Coupon",
        "Remove_Coupon" :  "➖ Remove Coupon" ,
        "upgrade_plan_message": "🔒 To unlock this feature, please upgrade your plan.\n📞 Contact us at [WhatsApp](https://wa.me/201554516636).",
        "choose_theme": "Please choose a theme:",
        "theme_selected_message": "✅ You have successfully selected {theme}. Enjoy your new look!",
        "preview": "Preview",
        "select": "Select",
        "settings_prompt": "⚙️ Settings:\nChoose an option below:",
        "add_another_account": "➕ Add Another Account",
        'switch_account_success': "✅ You have successfully switched to the account: {account_name}.",
        'buttons': {
            'add_product': "➕ Add Product",
            'edit_product': "✏️ Edit Product",
            'delete_product': "❌ Delete Product",
            'delete_category': "🗑️ Delete Category",
            'edit_store_info': "🛠️ Edit Store Info",
            'get_website_qr': "🌐 Get Website & QR Code",
            'see_orders': "see orders",
            'get_analytics': "📊 View Analytics",
            'add_account': "Add Account",
            'choose_product': "Choose a product to edit:",
            'edit_style' : "🎨 Edit Website Style",
            'edit_category': '✏️ Edit Category',
            'add_category': '➕ Add Category',
            'delete_category': '❌ Delete Category',
            'yes': "Yes",
            'delete': "Delete",
            'no': "No",
            'help': "Ask For Help",
            'cancel': "Cancel",
            'add_cover': "Add Cover",
            'delete_cover': "Delete Cover",
            "settings": "⚙️ Settings"
        }
    },
    'ar': {
        'welcome_back': "مرحبًا بك مجددًا، {username}! 🎉\n\n",
        'welcome_new': "مرحبًا بك في البوت! 🎉\n\n",
        'commands': "يمكنك استخدام الأوامر التالية:",
        'no_account': "يجب عليك إنشاء حساب أولاً.",
        'provide_category': "يرجى تقديم الفئة للمنتج.",
        'unable_to_determine_chat_id': "غير قادر على تحديد معرف المحادثة.",
        'category_confirmation': "الفئة '{category_name}' غير موجودة لهذا الحساب. هل تريد إنشاءها؟",
        'category_creation_success': "تم إنشاء الفئة '{category_name}'  بنجاح! يرجى تقديم اسم المنتج لاضافته. اول الضغط على الغاء",
        'item_name_prompt': "يرجى تقديم اسم المنتج.",
        'item_price_prompt': "يرجى تقديم السعر للمنتج.",
        'invalid_price': "سعر غير صالح. يرجى إدخال قيمة رقمية.",
        'awaiting_description': "يرجى تقديم وصف للمنتج.",
        'awaiting_image': "يرجى إرسال صورة للمنتج.",
        'create_account_first': "تحتاج إلى إنشاء حساب أولاً باستخدام /add_account.",
        'no_products_available': "لا توجد منتجات متاحة للحذف.",
        'no_products': "لا توجد منتجات متاحة.",
        'select_product_to_delete': "اختر المنتج الذي تريد حذفه:",
        'cancel': "إلغاء",
        'error_occurred': "حدث خطأ: {error}",
        'downloading_image': "جاري تنزيل صورة المنتج، قد يستغرق هذا بضع لحظات...",
        'image_downloaded_successfully': "تم تنزيل صورة المنتج بنجاح.",
        'product_added_successfully': "🎉 تم إضافة المنتج '{item}' بنجاح!",
        'visit_product_page': "قم بزيارة صفحة منتجك على: {url}",
        'control_over_all_things': "تحكم في كل شيء! 🎉\n\n",
        'add_product': "➕ إضافة منتج",
        'edit_product': "✏️ تعديل منتج",
        'delete_product': "❌ حذف منتج",
        'delete_category': "🗑️ حذف فئة",
        'edit_store_info': "🛠️ تعديل معلومات المتجر",
        'get_website_qr': "🌐 الحصول على الموقع ورمز QR",
        'image_download_error': 'حدث خطأ أثناء تنزيل صورة المنتج: {error}',
        'product_deleted': "تم حذف المنتج '{product_name}' بنجاح!",
        'product_not_exist': "المنتج المحدد غير موجود.",
        'video_upload': "لقد قمت بتحميل فيديو. يرجى تحميل صورة بدلاً من ذلك.",
        'document_upload': "لقد قمت بتحميل مستند. يرجى تحميل صورة بدلاً من ذلك.",
        'no_image_upload': "يرجى تحميل صورة.",
        'read_message_again': "يرجى قراءة الرسالة مرة أخرى.",
        'add_account': "إضافة حساب",
        'website_url': "رابط موقعك هو: {website_url}",
        'qr_code_caption': "إليك رمز الاستجابة السريعة الخاص بك.",
        'no_account_found': "لم يتم العثور على حساب. يرجى إضافة حساب أولاً.",
        'no_categories_available': "لا توجد فئات متاحة للحذف.",
        'select_category_to_delete': "حدد الفئة التي تريد حذفها:",
        'edit_name': "تعديل الاسم",
        'edit_price': "تعديل السعر",
        'edit_image': "تعديل الصورة",
        'selected_product': "لقد اخترت: {}. اختر ما تريد تعديله:",
        'video_for_logo': 'لقد قمت بتحميل فيديو للشعار. يرجى تحميل صورة كشعار للمحل.',
        'video_for_product_image': 'لقد قمت بتحميل فيديو لصورة المنتج. يرجى تحميل صورة للمنتج بدلاً من ذلك.',
        'general_video_upload': 'لقد قمت بتحميل فيديو. يرجى تحميل صورة بدلاً من ذلك إذا كنت تنوي تحميل شعار أو صورة منتج.',
        'product_update_success': "تم تحديث المنتج '{0}' بنجاح.",
        'edit_product_name': "يرجى إرسال الاسم الجديد للمنتج.",
        'edit_product_price': "يرجى إرسال السعر الجديد للمنتج.",
        'edit_product_image': "يرجى تحميل الصورة الجديدة للمنتج.",
        'upload_product_image': "يرجى تحميل صورة المنتج.",
        'product_not_found': "لم يتم العثور على المنتج.",
        'error_message': "حدث خطأ: {0}",
        'enter_new_title': "يرجى إدخال العنوان الجديد لمتجرك.",
        'process_canceled': "تم إلغاء العملية. يمكنك البدء مرة أخرى باستخدام /start.",
        'price_updated': "تم تحديث سعر المنتج إلى: {new_price}",
        'edit_logo': "تعديل الشعار",
        'edit_title': "تعديل العنوان",
        'edit_color': "تعديل اللون",
        'create_new_category': 'إنشاء فئة جديدة',
        'provide_category': 'يرجى اختيار فئة أو إنشاء فئة جديدة:',
        'cancel': "إلغاء",
        'what_to_edit': "ماذا تريد أن تعدل؟",
        'edit_primary_color': "تعديل اللون الأساسي",
        'edit_secondary_color': "تعديل اللون الثانوي",
        'which_color_to_edit': "أي لون تريد تعديله؟",
        'send_primary_color': "يرجى إرسال اللون الأساسي الجديد بصيغة هكس (مثل: #0E214B).",
        'send_secondary_color': "يرجى إرسال اللون الثانوي الجديد بصيغة هكس (مثل: #3F68DE).",
        'invalid_hex_format': "تنسيق هكس غير صالح! يرجى إرسال اللون بصيغة هكس (مثل: #0E214B).",
        'account_not_found': "لا يوجد حساب. يرجى إنشاء حساب أولاً باستخدام /add_account.",
        'primary_color_updated': "✅ تم تحديث لونك الأساسي إلى {new_color} بنجاح!",
        'secondary_color_updated': "✅ تم تحديث لونك الثانوي إلى {new_color} بنجاح!",
        'upload_logo': "يرجى تحميل صورة الشعار الجديد.",
        'upload_logo_image': "يرجى تحميل صورة الشعار.",
        'logo_updated': "تم تحديث الشعار بنجاح! 🎉",
        'error_updating_logo': "حدث خطأ أثناء تحديث الشعار",
        'title_updated': "✅ تم تحديث عنوانك إلى '{new_title}' بنجاح!",
        'error_updating_title': "حدث خطأ أثناء تحديث العنوان",
        'product_name_updated': "تم تحديث اسم المنتج إلى: {new_name}",
        'product_image_updated': "تم تحديث صورة المنتج بنجاح.",
        'product_not_found': "المنتج غير موجود.",
        'category_deleted': "تم حذف الفئة '{category_name}' بنجاح.",
        'category_delete_error': "حدث خطأ أثناء حذف الفئة: {error_message}",
        'send_username': ('يرجى إرسال **اسم المستخدم** لمتجرك.\n\n'
                         'سيكون اسم المستخدم جزءًا من عنوان URL الخاص بموقع متجرك، كالتالي:\n'
                         '👉 tidy-taps.c*m/s/اسم-المستخدم-الخاص-بك\n\n'),
        'send_logo': 'الآن يرجى إرسال **الشعار** (كصورة) لمتجرك.',
        'downloading_logo': 'جارٍ تحميل الشعار الخاص بك، قد يستغرق الأمر بضع لحظات...',
        'logo_downloaded': 'تم تنزيل الشعار بنجاح.',
        'ask_title': 'الآن يرجى إرسال **عنوان المتجر**.',
        'invalid_image_format': 'الملف المرفوع ليس تنسيق صورة صالح. يرجى تحميل ملف .jpg أو .jpeg أو .png أو .gif.',
        'error_downloading_logo': 'حدث خطأ أثناء تحميل الشعار: {}',
        'ask_phone_number': 'أخيرًا، يرجى إرسال رقم الهاتف WhatsApp للحساب.',
        'invalid_phone_number': 'رقم الهاتف غير صالح. يرجى إدخال رقم هاتف صالح.\nبالنسبة لمصر: 01XXXXXXXXX\nبالنسبة للمغرب: \u200E+212XXXXXXXXX أو 0XXXXXXXXX.',
        'user_not_found': 'لا يوجد مستخدم بالمعرف 1.',
        'account_added_success': '🎉 تم إضافة الحساب بنجاح!\n\nيمكنك الآن إضافة منتج جديد لحسابك عن طريق الضغط على زر "إضافة منتج" أدناه. اتبع التعليمات لتحديد فئة المنتج، الاسم، السعر، الوصف، والصورة.',
        'welcome_message': 'يمكنك التحكم في كل شيء! 🎉\n\n',
        'commands_prompt': 'يمكنك استخدام الأوامر التالية:',
        'username_taken': 'اسم المستخدم الذي قدمته مأخوذ بالفعل. يرجى اختيار اسم مستخدم مختلف والمحاولة مرة أخرى.',
        'enter_new_category': 'يرجى إدخال اسم الفئة الجديدة.',
        'help': "للمساعدة الإضافية، تواصل بنا على الواتساب: \n wa.me/+201554516636",
        'edit_delivery_fees': 'تعديل رسوم التوصيل',
        'photo_required': "يرجى إرسال صورة الاشعار، وليس نصًا أو أي نوع آخر من الملفات.",
        'ask_delivery_fee': 'هل ترغب في تحديد رسوم التوصيل لمتجرك؟',
        'enter_delivery_fee': 'يرجى إدخال مبلغ رسوم التوصيل:',
        'delivery_fee_set': 'تم تعديل رسوم التوصيل إلى: {}',
        'invalid_delivery_fee': 'إدخال غير صالح. يرجى إدخال رقم صالح لرسوم التوصيل.',
        'no_delivery_fee_set': 'لم يتم تعديل رسوم التوصيل.',
        'ask_upload_another_photo': 'هل تريد تحميل صورة أخرى؟',
        'invalid_image_type': 'من فضلك قم برفع صورة صالحة.',
        'no_more_photos': 'لا توجد صور أخرى لتحميلها.',
        'edit_contacts': "تعديل جهات الاتصال",  # New entry for editing contacts
        'edit_addresses': "تعديل العناوين",  # New entry for editing addresses
        'edit_social_media': "تعديل وسائل التواصل الاجتماعي",
        'choose_contact_to_edit_or_create': 'اختر جهة اتصال لتعديلها أو إنشاء واحدة جديدة:',
        'create_new_contact': '➕ إنشاء جهة اتصال جديدة',
        'select_contact': "يرجى اختيار جهة اتصال لتعديلها أو إنشاء جهة اتصال جديدة:",
        'enter_new_contacts': "يرجى إدخال رقم الهاتف لجهة الاتصال الجديدة:",
        'contact_added': "تمت إضافة رقم هاتف جهة الاتصال بنجاح.",
        'invalid_phone': "يرجى إدخال رقم هاتف صالح.",
        'edit_contact_phone': "يرجى إدخال رقم الهاتف الجديد لجهة الاتصال هذه:",
        'contact_not_found': "لم يتم العثور على جهة الاتصال المحددة.",
        'contact_updated': "تم تحديث تفاصيل جهة الاتصال.",
        'delete_contact': "حذف جهة اتصال",
        'select_action': "يرجى تحديد إجراء:",
        'select_contact_to_delete': "يرجى اختيار جهة الاتصال لحذفها:",
        'confirm_contact_delete': "هل أنت متأكد أنك تريد حذف هذه جهة الاتصال؟",
        'contact_deleted': "تم حذف جهة الاتصال بنجاح.",
        'confirm': "نعم، احذف",
        'enter_new_address': "يرجى إدخال العنوان الجديد:",
        'edit_addresses': "تعديل العناوين",
        'create_new_address': "إضافة عنوان جديد",
        'select_address': "اختر عنوانًا لتعديله أو أضف عنوانًا جديدًا:",
        'editing_address': "تعديل العنوان",
        'enter_new_addresses': "يرجى إدخال العنوان الجديد:",
        'address_added': "تمت إضافة العنوان بنجاح.",
        'address_updated': "تم تحديث العنوان بنجاح.",
        'address_deleted': 'تم حذف العنوان بنجاح.',
        'address_not_found': 'العنوان الذي تحاول حذفه غير موجود.',
        'operation_cancelled': 'تم إلغاء العملية.',
        'select_address_to_delete': 'يرجى اختيار عنوان لحذفه:',
        'delete_address': 'حذف العنوان',
        'edit_social_media': 'تعديل وسائل التواصل الاجتماعي',
        'select_social_media': 'اختر منصة وسائل التواصل الاجتماعي للتعديل:',
        'edit_facebook': 'تعديل رابط فيسبوك',
        'edit_instagram': 'تعديل رابط انستغرام',
        'edit_whatsapp': 'تعديل رابط واتساب',
        'edit_tiktok': 'تعديل رابط تيك توك',
        'enter_facebook_link': 'الرجاء إدخال رابط فيسبوك الخاص بك:',
        'enter_instagram_link': 'الرجاء إدخال رابط انستغرام الخاص بك:',
        'enter_whatsapp_link': 'الرجاء إدخال رابط واتساب الخاص بك:',
        'enter_tiktok_link': 'الرجاء إدخال رابط تيك توك الخاص بك:',
        'social_media_updated': 'تم تحديث رابط وسائل التواصل الاجتماعي بنجاح!',
        'no_social_media': 'لا توجد روابط وسائل التواصل الاجتماعي. يرجى إضافتها أولاً.',
        'invalid_instagram_link': 'يرجى إدخال رابط إنستغرام صالح يبدأ بـ "instagram.com" أو "https://www.instagram.com/" أو "www.instagram.com".',
        'social_media_instagram_updated': 'تم تحديث رابط إنستغرام بنجاح.',
        'invalid_whatsapp_link': 'يرجى إدخال رابط واتساب صالح يبدأ بـ "wa.me/".',
        'social_media_whatsapp_updated': 'تم تحديث رابط واتساب بنجاح.',
        'invalid_tiktok_link': 'يرجى إدخال رابط تيك توك صالح يبدأ بـ "tiktok.com".',
        'social_media_tiktok_updated': 'تم تحديث رابط تيك توك بنجاح.',
        'invalid_facebook_link': 'يرجى إدخال رابط فيسبوك صالح يبدأ بـ "facebook.com".',
        'social_media_facebook_updated': 'تم تحديث رابط فيسبوك بنجاح.',
        'do_you_want_to_add_options': "❓ هل تريد إضافة خيارات لهذا المنتج؟ 🛍️",
        'provide_option_title': "🏷️ يرجى تقديم عنوان لهذا الخيار (مثل: الحجم او اللون او إضافات):",
        'provide_option_values': "الآن، يرجى إدخال القيم لهذا الخيار (مثل: صغير، متوسط، كبير)، مفصولة بفواصل:",
        'option_added_successfully': "تمت إضافة الخيار بنجاح!",
        'add_more_options': "هل تريد إضافة المزيد من الخيارات لهذا المنتج؟",
        'provide_single_option_value': "🔢 يرجى إدخال قيمة لهذا الخيار (مثل: صغير, أحمر):",
        'provide_single_option_price': "💰 الآن، يرجى إدخال السعر لـ '{value}' (سيتم إضافة هذا السعر إلى سعر المنتج. إذا لم يكن هناك سعر إضافي، أدخل 0):",
        'add_more_option_values': "هل تريد ادخال قيمه اخرى لهذا الخيار",
        'options_completed': "✅ لقد انتهيت من إضافة الخيارات.",
        'options_completed': "✅ لقد انتهيت من إضافة الخيارات.",
        'add_another_option_title': "➕ هل ترغب في إضافة عنوان خيار آخر؟",
        'edit_option': "تعديل الخيارات",
        'choose_option_to_edit': "اختر خيارًا للتعديل:",
        'edit_option_title': "تعديل عنوان الخيار",
        'edit_option_choices': "تعديل قيم الخيارات",
        'enter_new_option_title': "أدخل العنوان الجديد للخيار:",
        'option_title_updated': "تم تحديث عنوان الخيار إلى: {0}",
        'enter_new_choice_value': "أدخل القيمة الجديدة لهذا الخيار:",
        'choice_value_updated': "تم تحديث قيمة الخيار إلى: {0}",
        'choose_choice_to_edit_or_add': "اختر خيارًا لتعديله، أو أضف خيارًا جديدًا:",
        'add_new_choice': "إضافة خيار جديد",
        'option_not_exist': "هذا الخيار غير موجود.",
        'no_options_to_edit': "لا توجد خيارات لهذا المنتج.",
        'choice_not_exist': "هذا الخيار غير موجود.",
        'edit_option_prompt': "أنت تقوم بتعديل الخيار: {0}. ماذا تريد أن تفعل؟",
        'edit_choice_value': "تعديل القيمة",  # Button label for editing the choice name/value
        'edit_choice_price': "تعديل السعر",  # Button label for editing the choice price
        'choose_edit_action': "ماذا تريد تعديل '{0}'؟",  # Message asking what to edit, where {0} is the choice name
        'choice_price_updated': "تم تحديث سعر الخيار إلى '{0}'.",  # Message confirming the price change
        'enter_new_price': "💰 الرجاء إدخال السعر الجديد لـ '{0}' (إذا لم يكن هناك زيادة على السعر، أدخل 0):",  # Message asking for the new price, {0} is the choice name
        'invalid_price': "إدخال غير صالح! الرجاء إدخال سعر صالح.",
        'enter_new_choice_name': "الرجاء إدخال اسم الخيار الجديد:",
        'enter_new_choice_price': "💰 الرجاء إدخال سعر الخيار الجديد (إذا لم يكن هناك سعر إضافي، أدخل 0):",
        'new_choice_added': "تمت إضافة الخيار الجديد '{0}' بسعر {1} بنجاح.",
        'add_new_option': "➕ إضافة خيار جديد",
        'enter_option_name': "📋 الرجاء إدخال اسم الخيار الجديد (مثلاً: اللون أو الحجم):",
        'enter_choice_name': "🏷️ الرجاء إدخال اسم الخيار (مثلاً: أحمر، أزرق):",
        'enter_choice_price': "💰 الرجاء إدخال السعر لهذا الخيار:",
        'add_another_choice_prompt': "➕ هل تريد إضافة خيار آخر؟",
        'finished_adding_choices': "✅ لقد انتهيت من إضافة الخيارات لهذا الخيار.",
        'remove_option': "❌ إزالة الخيار",
        'confirm_remove_option': "هل أنت متأكد أنك تريد إزالة الخيار '{}؟' هذا الإجراء لا يمكن التراجع عنه.",
        'option_removed': "تمت إزالة الخيار بنجاح.",
        'removal_canceled': "تم إلغاء إزالة الخيار.",
        'edit_whatsapp_number': "تعديل رقم الواتساب",
        'enter_new_phone_number': "يرجى إدخال رقم الواتساب الجديد الخاص بك:",
        'whatsapp_number_updated': "تم تحديث رقم الواتساب الخاص بك بنجاح.",
        'invalid_phone_number': "رقم الهاتف الذي أدخلته غير صالح. يرجى التأكد من أنه يبدأ بعلامة '+' متبوعة برمز الدولة (مثل +1 للولايات المتحدة، +44 للمملكة المتحدة) وأن يحتوي على أرقام فقط.",
        'edit_description': "تعديل الوصف",
        'enter_new_description': "يرجى إدخال الوصف الجديد للمنتج:",
        'description_updated': "تم تحديث وصف المنتج بنجاح.",
        'edit_cover': "تعديل الغلاف",
        'upload_cover_instruction': "يرجى تحميل صورة غلاف لمتجرك. ستظهر في أعلى المتجر.",
        'cover_uploaded_successfully': "تم تحميل صورة الغلاف بنجاح!",
        "upload_another_cover_inst" : "يرجى تحميل صورة غلاف اخرى لمتجرك",
        'upload_another_cover': "هل ترغب في تحميل صورة غلاف أخرى؟",
        'cover_upload_complete': "اكتمل تحميل الغلاف. شكرًا لك!",
        'upload_error': "حدث خطأ أثناء تحميل صورة الغلاف. يرجى المحاولة مرة أخرى.",
        'cover_downloaded_successfully': "تم تحميل صورة الغلاف بنجاح!",
        'ask_upload_another_cover': "هل ترغب في تحميل صورة غلاف أخرى؟",
        'cover_download_error': "حدث خطأ أثناء تنزيل صورة الغلاف: {error}",
        'invalid_image_type': "يرجى إرسال ملف صورة صالح.",
        'choose_cover_action': "هل ترغب في إضافة غلاف جديد أو حذف غلاف موجود؟",
        'upload_cover_instruction': "يرجى تحميل صورة غلاف جديدة.",
        'cover_deleted': "تم حذف صورة الغلاف.",
        'cover_not_found': "لم يتم العثور على غلاف لحذفه.",
        'choose_delivery_option': "اختر خيارًا لرسوم التوصيل:",
        'enter_delivery_details': "يرجى إدخال المدينة لرسوم التوصيل الجديدة.",
        'choose_delivery_to_edit': "اختر إدخال التوصيل الذي تريد تعديله.",
        'choose_delivery_to_delete': "اختر إدخال التوصيل الذي تريد حذفه.",
        'delivery_added': 'تم إضافة التوصيل إلى %s مع رسوم قدرها %s.',
        'delivery_deleted': "تم حذف التوصيل للمدينة %s.",
        'add_delivery': "إضافة توصيل",
        'delete_delivery': "حذف التوصيل",
        "get_analytics": (
            "📊 *تحليلات لحسابك*\n"
            "إجمالي المشاهدات: {total_views}\n"
            "إجمالي الزيارات: {total_visits}\n"
        ),
        "loading_message": "جاري تحميل بيانات التحليلات... من فضلك انتظر.",
        "failed_fetch": "فشل في جلب التحليلات. كود الحالة: {status_code}",
        'too_many_images': "يمكنك تحميل ما يصل إلى {max_images} صورة فقط. يرجى المحاولة مرة أخرى بعدد أقل من الصور.",
        'choose_category_action': "اختر إجراءً للفئة:",
        'choose_category_to_edit': "اختر فئة للتعديل:",
        'enter_new_category_name': "يرجى إدخال الاسم الجديد للفئة:",
        'category_updated_successfully': "تم تحديث الفئة بنجاح.",
        'category_not_found': "لم يتم العثور على الفئة المحددة.",
        'confirm_delete_message': "هل أنت متأكد أنك تريد حذف هذه الفئة؟",
        'add_image': "➕ إضافة صورة",
        'remove_image': "❌ إزالة الصورة",
        'choose_image_action': "يرجى اختيار إجراء لصورة المنتج:",
        'choose_image_to_remove': "يرجى اختيار الصورة لإزالتها:",
        'no_images_to_remove': "لا توجد صور متاحة للإزالة.",
        'image_removed_success': "تمت إزالة الصورة بنجاح.",
        'image_added_success': "تمت إضافة الصورة بنجاح إلى المنتج!",
        'edit_offer': " تعديل العرض",
        'enter_offer': "السعر الحالي لـ *{product_name}* هو {product_price}.\nيرجى إدخال سعر العرض الجديد لهذا المنتج:",
        'invalid_offer': "قيمة العرض يجب أن تكون رقمًا صالحًا. حاول مرة أخرى.",
        'offer_updated': "تم تحديث العرض لـ *{product_name}* بنجاح إلى {new_offer}.",
        'error_occurred': "حدث خطأ أثناء تحديث العرض. حاول مرة أخرى لاحقًا.",
        'unrecognized_message': "لم أفهم ذلك. يرجى استخدام الخيارات المتاحة.",
        'edit_currency': "تغيير العملة",
        'select_currency': "يرجى اختيار العملة:",
        'currency_selected': "لقد اخترت العملة:",
        'previous': "⬅️ السابق",
        'next': "التالي ➡️",
        'currency_updated': "تم تحديث عملتك إلى: {currency}.",
        'upload_new_category_picture': "يرجى تحميل صورة الفئة الجديدة.",
        'category_picture_updated': "تم تحديث صورة الفئة بنجاح!",
        'invalid_picture_format': "تنسيق غير صالح. يرجى تحميل صورة صالحة.",
        'no_category_selected': "لم يتم اختيار فئة للتعديل.",
        'downloading_category_image': "جاري تنزيل صورة الفئة، يرجى الانتظار...",
        'category_image_downloaded_successfully': "تم تنزيل صورة الفئة بنجاح!",
        "edit_coupons": "كوبونات الخصم",
        "ask_for_edit_coupons":"ماذا تريد ان تفعل فى كوبونات الخصم",
        'enter_coupon_code': "يرجى إدخال رمز القسيمة: مثل (newYear2025)",
        'enter_coupon_amount': "يرجى إدخال قيمة القسيمة:",
        'invalid_amount': "قيمة غير صالحة. يرجى إدخال رقم صالح.",
        'coupon_added': "تمت إضافة القسيمة بنجاح! 🎉",
        'select_coupon_to_remove': "اختر القسيمة التي تريد إزالتها:",
        'coupon_removed': "تمت إزالة القسيمة بنجاح! 🗑️",
        'coupon_not_found': "لم يتم العثور على القسيمة. قد تكون تمت إزالتها بالفعل.",
        'no_coupons': "لا توجد قسائم لإزالتها.",
        "Add_Coupon" : "➕ اضافة كوبون",
        "Remove_Coupon" :  "➖ حذف كوبون" ,
        "upgrade_plan_message": "🔒 لفتح هذه الميزة، يرجى ترقية خطتك.\n📞 تواصل معنا على [واتساب](https://wa.me/201554516636).",
        "choose_theme": "يرجى اختيار شكل:",
        "theme_selected_message": "✅ لقد قمت باختيار {theme} بنجاح. استمتع بالمظهر الجديد!",
        "preview": "مشاهدة",
        "select": "اختيار",
        "settings_prompt": "⚙️ الإعدادات:\n\nاختر خيارًا أدناه:",
        "add_another_account": "➕ إضافة حساب آخر",
        'switch_account_success': "✅ لقد تم التبديل إلى الحساب: {account_name} بنجاح.",
        'buttons': {
            'add_product': "📦 إضافة منتج",
            'edit_product': "✏️ تعديل منتج",
            'delete_product': "❌ حذف منتج",
            'edit_store_info': "🛠️ تعديل معلومات المتجر",
            'get_website_qr': "🌐 الحصول على الموقع ورمز QR",
            'get_analytics': "📊 عرض التحليلات",
            'see_orders': "رؤيه الطلبات",
            'add_account': "إضافة حساب",
            'choose_product': "اختر منتجًا لتعديله:",
            'add_cover': "إضافة غلاف",
            'edit_style': "🎨 تعديل شكل الموقع",
            'edit_category': '✏️ تعديل الفئة',
            'add_category': '➕ إضافة فئة',
            'delete_category': '❌ حذف الفئة',
            'delete_cover': "حذف غلاف",
            'delete': "حذف",
            'yes': "نعم",
            'no': "لا",
            'help': "طلب المساعدة",
            'cancel': "إلغاء",
            "settings": "⚙️ الإعدادات"
        }
    }
    # Add more languages as needed,
}




def get_message(user, key):
    # Fallback to English if no translation exists
    lang = user.language or 'en'
    return MESSAGES.get(lang, MESSAGES['en']).get(key, MESSAGES['en'][key])


async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("inside add_account")
    selected_lang = context.user_data.get('lang', 'en')  # Default to 'en' if no language is set
    
    if update.message:
        await update.message.reply_text(
            MESSAGES[selected_lang]['send_username']
        )
        context.user_data['state'] = 'awaiting_username'

    elif update.callback_query:
        await update.callback_query.message.reply_text(
            MESSAGES[selected_lang]['send_username']
        )
        context.user_data['state'] = 'awaiting_username'

# Handle messages (general handler to manage flow state)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state = context.user_data.get('state')
    selected_lang = context.user_data.get('lang')
    account = context.user_data.get('account')
    print("user_state")
    print(user_state)
    if not account:
        chat_id = context.user_data.get('chat_id', update.message.chat.id)
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            print("wewewe")
            pass
                
    # Set the language based on the account if not already set
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model
    print("we are hereee")
    # If language is still not found, show start message instead
    if selected_lang not in MESSAGES:
        await start(update, context)
        return
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
    elif user_state == 'awaiting_contact':
        await handle_contact(update, context)
    elif user_state == 'awaiting_item_name':
        await handle_item_name(update, context)
    elif user_state == "enter_coupon_code":
        await process_coupon_code(update, context)
    elif user_state == 'enter_coupon_amount':
        print("wewe")
        await process_coupon_amount(update, context)
    
    elif user_state == 'awaiting_facebook_link':
        await edit_facebook_link(update, context)

    elif user_state == 'awaiting_instagram_link':
        await edit_instagram_link(update, context)

    elif user_state == 'awaiting_whatsapp_link':
        await edit_whatsapp_link(update, context)

    elif user_state == 'awaiting_tiktok_link':
        await edit_tiktok_link(update, context)
    elif user_state == 'WAITING_FOR_OFFER':
        user_message = update.message.text  # Get the user's message
        chat_id = update.message.chat.id
        account = context.user_data.get('account')
        selected_lang = account.language if account else 'en'

        # Check if the bot is waiting for an offer input
        current_state = context.user_data.get('state')
        if current_state == 'WAITING_FOR_OFFER':
            # Retrieve the product from context
            product = context.user_data.get('product')
            if not product:
                await update.message.reply_text(
                    MESSAGES[selected_lang]['product_not_exist']
                )
                return

            try:
                # Validate and update the offer value
                new_offer = user_message.strip()
                if not new_offer.isnumeric() and not new_offer.replace('.', '', 1).isdigit():
                    await update.message.reply_text(
                        MESSAGES[selected_lang]['invalid_offer']
                    )
                    return

                # Convert the offer to a numeric type (e.g., float)
                new_offer = float(new_offer)

                # Update the product's old_price, price, offer, and hasOffer fields
                product.old_price = product.price  # Set the old_price to the current price
                product.price = new_offer          # Set the new price to the offer
                product.offer = new_offer          # Save the offer value
                product.hasOffer = True            # Mark the product as having an offer
                await sync_to_async(product.save)()  # Save changes asynchronously

                # Notify the user of the successful update
                await update.message.reply_text(
                    MESSAGES[selected_lang]['offer_updated'].format(
                        product_name=product.item,
                        new_offer=new_offer
                    )
                )
                await show_start_message(update, context, account)
                
                # Reset the state
                context.user_data['state'] = None

            except Exception as e:
                # Handle any unexpected errors
                await update.message.reply_text(
                    MESSAGES[selected_lang]['error_occurred']
                )
                print(f"Error updating offer: {e}")
        else:
            # Handle other messages (if not in a specific state)
            await update.message.reply_text(
                MESSAGES[selected_lang]['unrecognized_message']
            )
    
    elif user_state == 'awaiting_price':
        await handle_price(update, context)
    elif user_state == "awaiting_cover_upload":
        await handle_cover_upload(update, context)

    elif user_state == "awaiting_fee_input":
        await handle_city_input(update, context)
    elif user_state == "adding_delivery_city":
        await handle_city_input(update, context)

    elif user_state == 'awaiting_address_details':
        await start_creating_address(update, context)

    elif user_state == 'awaiting_option_title'  or user_state == "awaiting_new_option_name":
        print("we are in awaiting option title")
        await handle_option_title(update, context)

    elif user_state == "awaiting_single_option_value":
        await handle_option_value(update, context)
    elif user_state == "awaiting_single_option_price":
        await handle_option_price(update, context)

    elif user_state == 'awaiting_description':
        await handle_description(update, context)

    elif user_state == 'awaiting_new_address':
        await handle_new_address_input(update, context)

    elif user_state == 'awaiting_new_contact':
        await handle_contact_input(update, context)

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
    elif user_state =="waiting_for_primary_color":
        await handle_primary_color_response(update, context)
    elif user_state =="waiting_for_secondary_color":
        await handle_secondary_color_response(update, context)
    elif user_state == 'awaiting_delivery_fee':
        await handle_edit_delivery_fees(update, context)

    elif user_state == 'awaiting_new_option_title':
        print("we are in awaiting_new_option_title")
        await receive_new_option_title(update, context)
    elif user_state == 'awaiting_choice_value':
        await receive_new_choice_value(update, context)

    elif user_state == "awaiting_edit_new_price_choice":
        await receive_new_price(update, context)

    elif user_state == "awaiting_choice_name":
        await receive_new_choice_name(update, context)
    elif user_state == "awaiting_choice_price":
        await receive_new_choice_price(update, context)
    elif user_state == "awaiting_phone_number":
        await edit_whatsapp_number(update, context)
    elif user_state == "awaiting_edit_description":
        await handle_edit_description(update, context)
    elif 'category_id_to_edit' in context.user_data:
        await handle_new_category_name(update, context)
    else:
        print("we are in else in message handle")
        if not account:
                try:
                    account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
                    context.user_data['account'] = account  # Cache the account in user_data
                except Account.DoesNotExist:
                    keyboard = [
                        [InlineKeyboardButton(MESSAGES['en']['buttons']['add_account'], callback_data="add_account")],
                        [InlineKeyboardButton(MESSAGES['en']['buttons']['cancel'], callback_data="cancel")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await update.callback_query.message.reply_text(
                        MESSAGES['en']['no_account'],
                        reply_markup=reply_markup
                    )
                    return
        else:
            await show_start_message(update, context, account)

async def handle_edit_delivery_fees(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        selected_lang = context.user_data.get('lang')

        if 'account' not in context.user_data:
            chat_id = context.user_data.get('chat_id', update.message.chat.id)
            try:
                account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
                context.user_data['account'] = account
            except Account.DoesNotExist:
                await update.message.reply_text(MESSAGES[selected_lang]['account_not_found'])
                return
                
        account = context.user_data.get('account')

        if not selected_lang and account:
            selected_lang = account.language  # Replace with the actual field name for language in your Account model

        print("selected_lang in edit delivery fees")
        print(selected_lang)
        delivery_fee = float(update.message.text)

        context.user_data['delivery_fee'] = delivery_fee

        # Confirm the fee
        await update.message.reply_text(MESSAGES[selected_lang]['delivery_fee_set'].format(delivery_fee))

        delivery_fee_str = str(delivery_fee)
        delivery, created = await sync_to_async(Delivery.objects.get_or_create)(
            account=account,
            defaults={'amount': delivery_fee_str}
        )
        if not created:  # If the delivery already exists, update it
            delivery.amount = delivery_fee_str
            await sync_to_async(delivery.save)()


        await show_start_message(update, context, account)
            
    except ValueError:
        await update.message.reply_text(MESSAGES[selected_lang]['invalid_delivery_fee'])

async def receive_new_option_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    
    option = context.user_data.get('option')

    if context.user_data.get('state') == 'awaiting_new_option_title':
        new_title = update.message.text

        # Update the option title
        option.name = new_title
        await sync_to_async(option.save)()

        await update.message.reply_text(MESSAGES[selected_lang]['option_title_updated'].format(new_title))

        # Reset the state
        context.user_data['state'] = None

async def receive_new_choice_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    
    choice = context.user_data.get('choice')

    if context.user_data.get('state') == 'awaiting_choice_value':
        new_choice_value = update.message.text

        # Update the choice value
        choice.name = new_choice_value
        await sync_to_async(choice.save)()

        await update.message.reply_text(MESSAGES[selected_lang]['choice_value_updated'].format(new_choice_value))

        # Reset the state
        context.user_data['state'] = None

async def receive_new_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    

    # Check if the state is correct for receiving the new price
    if context.user_data.get('state') == 'awaiting_edit_new_price_choice':
        new_price = update.message.text

        # Validate that the input is a number (basic validation)
        if not new_price.isdigit():
            await update.message.reply_text(MESSAGES[selected_lang]['invalid_price'])
            return

        # Get the choice from user_data
        choice = context.user_data.get('choice')

        # Update the price for the choice
        choice.price = new_price
        await sync_to_async(choice.save)()

        # Notify the user that the price has been updated
        await update.message.reply_text(MESSAGES[selected_lang]['choice_price_updated'].format(choice.name))


async def receive_new_choice_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    

    # Check the state
    if context.user_data.get('state') == 'awaiting_choice_name':
        new_choice_name = update.message.text
        context.user_data['new_choice_name'] = new_choice_name  # Cache the new choice name

        # Ask for the price of the new choice
        await update.message.reply_text(MESSAGES[selected_lang]['enter_new_choice_price'])

        # Update the state to await the price
        context.user_data['state'] = 'awaiting_choice_price'


async def receive_new_choice_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    
    menu_item = context.user_data.get('product')
    # Check the state
    if context.user_data.get('state') == 'awaiting_choice_price':
        new_choice_price = update.message.text

        # Basic validation to check if it's a valid number
        if not new_choice_price.isdigit():
            await update.message.reply_text(MESSAGES[selected_lang]['invalid_price'])
            return

        # Get the option and new choice name from user_data
        option = context.user_data.get('option')
        new_choice_name = context.user_data.get('new_choice_name')

        # Save the new choice to the database
        new_choice = await sync_to_async(MenuItemChoices.objects.create)(
            account=account,
            menuitem=menu_item,
            option=option,
            name=new_choice_name,
            price=new_choice_price
        )

        await update.message.reply_text(MESSAGES[selected_lang]['new_choice_added'].format(new_choice_name, new_choice_price))
        await show_start_message(update, context, account)

async def edit_whatsapp_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        
    if not selected_lang and account:
        selected_lang = account.language

    if context.user_data.get('state') == 'awaiting_phone_number':
        if validate_phone_number(user_message):
            # Store only digits for the phone number in the database
            cleaned_number = re.sub(r'[^\d]', '', user_message)
            account.phone_number = cleaned_number
            await sync_to_async(account.save)()
            await update.message.reply_text(MESSAGES[selected_lang]['whatsapp_number_updated'])
            await show_start_message(update, context, account)
        else:
            await update.message.reply_text(MESSAGES[selected_lang]['invalid_phone_number'])
        return


def validate_phone_number(phone_number):
    # Remove spaces, dashes, and parentheses
    phone_number = re.sub(r'[\s\-()]+', '', phone_number)

    # Validate Egyptian phone numbers (10 digits, starting with 01)
    if re.match(r'^01[0125][0-9]{8}$', phone_number):
        return True

    # Validate international phone numbers
    # Accepts formats like +201234567890 or +441632960961 (UK)
    # Country code should be 1-3 digits, followed by 4-14 digits
    # Added validation for numbers starting with digits only (without '+')
    if re.match(r'^\d{1,3}\d{4,14}$', phone_number) or re.match(r'^\+\d{1,3}\d{4,14}$', phone_number):
        return True

    return False


async def handle_edit_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    selected_lang = context.user_data.get('lang')

    if 'account' not in context.user_data:
        chat_id = context.user_data.get('chat_id', update.callback_query.message.chat.id)
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.message.reply_text(MESSAGES[selected_lang]['account_not_found'])
            return
            
    account = context.user_data.get('account')

    if not selected_lang and account:
        selected_lang = account.language


    if context.user_data.get('state') == 'awaiting_edit_description':
        product = context.user_data.get('product')
        if product:
            product.desc = user_message  # Update the product description
            await sync_to_async(product.save)()  # Save changes to the database
            await update.message.reply_text(MESSAGES[selected_lang]['description_updated'])
            await show_start_message(update, context, account)
            
        else:
            await update.message.reply_text(MESSAGES[selected_lang]['product_not_exist'])


async def edit_store_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')

    if 'account' not in context.user_data:
        chat_id = context.user_data.get('chat_id', update.callback_query.message.chat.id)
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.message.reply_text(MESSAGES[selected_lang]['account_not_found'])
            return
            
    account = context.user_data.get('account')

    if not selected_lang and account:
        selected_lang = account.language

    await update.callback_query.answer()

    # Improved button layout with emojis and better grouping
    keyboard = [
    [
        InlineKeyboardButton(f"🖼 {MESSAGES[selected_lang]['edit_logo']}", callback_data="edit_logo"),
        InlineKeyboardButton(f"🖼 {MESSAGES[selected_lang]['edit_cover']}", callback_data="edit_cover"),
    ],
    [
        InlineKeyboardButton(f"✏️ {MESSAGES[selected_lang]['edit_title']}", callback_data="edit_title"),
        InlineKeyboardButton(f"🎨 {MESSAGES[selected_lang]['edit_color']}", callback_data="edit_color"),
    ],
    [
        InlineKeyboardButton(f"🚚 {MESSAGES[selected_lang]['edit_delivery_fees']}", callback_data="edit_delivery_fees"),
        InlineKeyboardButton(f"📞 {MESSAGES[selected_lang]['edit_contacts']}", callback_data="edit_contacts"),
    ],
    [
        InlineKeyboardButton(f"🏠 {MESSAGES[selected_lang]['edit_addresses']}", callback_data="edit_addresses"),
        InlineKeyboardButton(f"📱 {MESSAGES[selected_lang]['edit_whatsapp_number']}", callback_data="edit_whatsapp_number"),

    ],
    [
        InlineKeyboardButton(f"💱 {MESSAGES[selected_lang]['edit_currency']}", callback_data="change_currency"),
        InlineKeyboardButton(f"🎟️ {MESSAGES[selected_lang]['edit_coupons']}", callback_data="edit_coupons"),
    ],
    [
        InlineKeyboardButton(f"🌐 {MESSAGES[selected_lang]['edit_social_media']}", callback_data="edit_social_media"),
    ],
    [
        InlineKeyboardButton(f"❌ {MESSAGES[selected_lang]['cancel']}", callback_data="cancel")
    ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['what_to_edit'], reply_markup=reply_markup)


async def handle_edit_delivery_fees(update, context):
    selected_lang = context.user_data.get('lang')
    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    
    # Define buttons for Add, Edit, and Delete delivery fees
    delivery_options_keyboard = [
        [
            InlineKeyboardButton(MESSAGES[selected_lang]['add_delivery'], callback_data="add_delivery"),
            #InlineKeyboardButton("✏️ Edit Delivery", callback_data="edit_existing_delivery"),
            InlineKeyboardButton(MESSAGES[selected_lang]['delete_delivery'], callback_data="delete_delivery"),
        ],
        [InlineKeyboardButton(MESSAGES[selected_lang]['cancel'], callback_data="cancel")]
    ]
    
    # Set up the reply markup for inline buttons
    reply_markup = InlineKeyboardMarkup(delivery_options_keyboard)
    
    # Send the message with inline buttons for delivery fee options
    await update.callback_query.message.reply_text(
        MESSAGES[selected_lang]['choose_delivery_option'], 
        reply_markup=reply_markup
    )

    # Set user state to "choosing_delivery_option"
    context.user_data['state'] = 'choosing_delivery_option'


# Handle adding delivery fee
async def handle_add_delivery(update, context):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing

    # Store the state of the user as adding delivery
    context.user_data['state'] = 'adding_delivery_city'

    # Prompt user to enter the city/area for the delivery fee
    await update.callback_query.message.reply_text(
        MESSAGES[selected_lang]['enter_delivery_details']  # Prompt to enter city and fee
    )

async def handle_city_input(update, context):
    selected_lang = context.user_data.get('lang')
    account = context.user_data.get('account')

    # Determine chat_id based on whether it's a message or callback query
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        await update.callback_query.answer()  # Acknowledge the callback query
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return

    # Use account language if selected_lang is missing
    if not selected_lang and account:
        selected_lang = account.language

    # If 'city' is not stored, ask for it
    if 'city' not in context.user_data:
        context.user_data['city'] = update.message.text
        await update.message.reply_text(MESSAGES[selected_lang]['enter_delivery_fee'])  # Ask for delivery fee
        context.user_data['state'] = 'awaiting_fee_input'

    # If 'fee' is not stored, save the delivery fee and create the Delivery
    elif 'fee' not in context.user_data:
        context.user_data['fee'] = update.message.text

        # Save the city and fee in the Delivery model (using sync_to_async for DB operations)
        city = context.user_data.get('city')
        fee = context.user_data.get('fee')

        # Creating delivery entry asynchronously
        await create_delivery(account, city, fee)

        await update.message.reply_text(MESSAGES[selected_lang]['delivery_added'] % (city, fee))

        # Clear stored data for this operation
        context.user_data.pop('city', None)
        context.user_data.pop('fee', None)
        

        # Reset the state
        context.user_data['state'] = None

        await show_start_message(update, context, account)

# Use sync_to_async on the database operation function
@sync_to_async
def create_delivery(account, city, fee):
    # Directly creating the Delivery record in the DB
    Delivery.objects.create(account=account, city=city, amount=fee)
# Handle edit delivery
async def handle_edit_delivery(update, context):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    
    await update.callback_query.message.reply_text(
        MESSAGES[selected_lang]['choose_delivery_to_edit']  # Prompt to select delivery to edit
    )

    # Store the state as editing delivery
    context.user_data['state'] = 'editing_delivery'


async def handle_delete_delivery(update, context):
    selected_lang = context.user_data.get('lang')
    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        await update.callback_query.answer()  # Acknowledge the callback query
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing

    # Fetch all cities associated with the account asynchronously
    deliveries = await sync_to_async(list)(Delivery.objects.filter(account=account))
    
    # Prepare the list of cities with delivery id
    cities = [(delivery.id, delivery.city) for delivery in deliveries]
    print("cities")
    print(cities)

    if not cities:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_deliveries_found'])
        return

    # Create inline buttons for each city
    keyboard = [
    [
        InlineKeyboardButton(city if city else "Unknown City", callback_data=f"delete_city_{id}")
    ]
    for id, city in cities
]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(
        MESSAGES[selected_lang]['choose_delivery_to_delete'],  # Prompt to select delivery to delete
        reply_markup=reply_markup
    )

    # Store the state as deleting delivery
    context.user_data['state'] = 'deleting_delivery'
async def handle_edit_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    account = context.user_data.get('account')

    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton(MESSAGES[selected_lang]['edit_primary_color'], callback_data="edit_primary_color")],
        [InlineKeyboardButton(MESSAGES[selected_lang]['edit_secondary_color'], callback_data="edit_secondary_color")],
        [InlineKeyboardButton(MESSAGES[selected_lang]['cancel'], callback_data="cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['which_color_to_edit'], reply_markup=reply_markup)

async def edit_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    
    product = context.user_data.get('product')

    # Fetch the options for the selected product
    options = await sync_to_async(list)(Option.objects.filter(Item=product))

    keyboard = []

    if not options:
        # If there are no options, show a button to add a new option
        keyboard.append([InlineKeyboardButton(MESSAGES[selected_lang]['add_new_option'], callback_data="add_new_option")])
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_options_to_edit'], reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # If there are options, show them with an additional button to add a new option
    for option in options:
        # Add edit button for each option
        keyboard.append([InlineKeyboardButton(option.name, callback_data=f"edit_option_{option.id}")])
        # Add remove button with option name for each option
        keyboard.append([InlineKeyboardButton(f"{MESSAGES[selected_lang]['remove_option']} ({option.name})", callback_data=f"remove_option_{option.id}")])

    # Add button for adding a new option
    keyboard.append([InlineKeyboardButton(MESSAGES[selected_lang]['add_new_option'], callback_data="add_new_option")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['choose_option_to_edit'], reply_markup=reply_markup)

async def handle_remove_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    query = update.callback_query
    await query.answer()

    # Extract the option ID from the callback data
    option_id = query.data.split('_')[-1]

    # Fetch the option to ensure it exists
    try:
        option = await sync_to_async(Option.objects.get)(id=option_id)
    except Option.DoesNotExist:
        await query.message.reply_text(MESSAGES[selected_lang]['option_not_exist'])
        return

    # Confirm removal with the user
    keyboard = [
        [InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['yes'], callback_data=f"confirm_remove_option_{option.id}")],
        [InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['no'], callback_data="cancel_remove_option")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        MESSAGES[selected_lang]['confirm_remove_option'].format(option.name),
        reply_markup=reply_markup
    )

async def handle_confirm_remove_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    query = update.callback_query
    await query.answer()

    if query.data.startswith("confirm_remove_option_"):
        option_id = query.data.split('_')[-1]

        try:
            # Remove the option
            await sync_to_async(Option.objects.filter(id=option_id).delete)()
            await query.message.reply_text(MESSAGES[selected_lang]['option_removed'])
        except Option.DoesNotExist:
            await query.message.reply_text(MESSAGES[selected_lang]['option_not_exist'])

    elif query.data == "cancel_remove_option":
        await query.message.reply_text(MESSAGES[selected_lang]['removal_canceled'])



async def handle_edit_option(update: Update, context: ContextTypes.DEFAULT_TYPE, option_id):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    

    try:
        option = await sync_to_async(Option.objects.get)(id=option_id)
        context.user_data['option'] = option  # Cache the option

        # Ask if the user wants to edit the title or the choices
        keyboard = [
            [InlineKeyboardButton(MESSAGES[selected_lang]['edit_option_title'], callback_data=f"edit_option_title_{option.id}")],
            [InlineKeyboardButton(MESSAGES[selected_lang]['edit_option_choices'], callback_data=f"edit_option_choices_{option.id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.message.reply_text(
            MESSAGES[selected_lang]['edit_option_prompt'].format(option.name),
            reply_markup=reply_markup
        )

    except Option.DoesNotExist:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['option_not_exist'])

async def add_new_choice(update: Update, context: ContextTypes.DEFAULT_TYPE, option_id):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    

    # Fetch the option using the option_id
    try:
        option = await sync_to_async(Option.objects.get)(id=option_id)
        context.user_data['option'] = option  # Cache the option in user_data
    except Option.DoesNotExist:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['option_not_exist'])
        return

    # Ask the user for the new choice name
    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['enter_new_choice_name'])
    
    # Set the state to indicate that we're waiting for the new choice name
    context.user_data['state'] = 'awaiting_choice_name'

async def handle_add_new_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    

    # Prompt user for the new option name
    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['enter_option_name'])
    
    # Set the state to track what we're asking for
    context.user_data['state'] = 'awaiting_new_option_name'

async def handle_add_another_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    

    query = update.callback_query
    await query.answer()

    if query.data == 'add_another_choice':
        # Ask for the next choice name
        context.user_data['state'] = 'awaiting_choice_name'
        await query.message.reply_text(MESSAGES[selected_lang]['enter_choice_name'])

    elif query.data == 'finish_adding_choices':
        # Finish adding options and choices
        context.user_data['state'] = None
        await query.message.reply_text(MESSAGES[selected_lang]['finished_adding_choices'])

async def edit_option_choices(update: Update, context: ContextTypes.DEFAULT_TYPE, option_id):
    print("we are in edit_option_choices func")
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    

    # Ensure that option is already set in context, or fetch it if necessary
    option = context.user_data.get('option')

    if option:
        try:
            # Fetch option from database if not already in context or incorrect option_id
            option = await sync_to_async(Option.objects.get)(id=option_id)
            context.user_data['option'] = option  # Store it in user_data
        except Option.DoesNotExist:
            await update.callback_query.message.reply_text(MESSAGES[selected_lang]['option_not_exist'])
            return

    # Fetch choices for this option
    choices = await sync_to_async(list)(MenuItemChoices.objects.filter(option=option))

    # Prepare the keyboard with current choices to edit or add new ones
    keyboard = []
    for choice in choices:
        keyboard.append([InlineKeyboardButton(f"{choice.name}", callback_data=f"edit_choice_{choice.id}")])

    # Add button to allow adding a new choice
    keyboard.append([InlineKeyboardButton(MESSAGES[selected_lang]['add_new_choice'], callback_data=f"add_new_choice_{option.id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        MESSAGES[selected_lang]['choose_choice_to_edit_or_add'],
        reply_markup=reply_markup
    )

async def handle_edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE, choice_id):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    
    
    # Fetch the choice from the database
    choice = await sync_to_async(MenuItemChoices.objects.get)(id=choice_id)
    
    # Ask the user if they want to edit the value or the price
    keyboard = [
        [InlineKeyboardButton(MESSAGES[selected_lang]['edit_choice_value'], callback_data=f"edit_choice_value_{choice.id}")],
        [InlineKeyboardButton(MESSAGES[selected_lang]['edit_choice_price'], callback_data=f"edit_choice_price_{choice.id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(
        MESSAGES[selected_lang]['choose_edit_action'].format(choice.name),
        reply_markup=reply_markup
    )


async def edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE, choice_id):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    

    try:
        choice = await sync_to_async(MenuItemChoices.objects.get)(id=choice_id)
        context.user_data['choice'] = choice  # Cache the choice

        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['enter_new_choice_value'])

        # Set state to awaiting choice input
        context.user_data['state'] = 'awaiting_choice_value'

    except MenuItemChoices.DoesNotExist:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['choice_not_exist'])



async def handle_edit_choice_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    
    
    
    query = update.callback_query
    await query.answer()

    # Extract choice ID from the callback data
    choice_id = query.data.split("_")[-1]

    try:
        # Fetch the choice by ID
        choice = await sync_to_async(MenuItemChoices.objects.get)(id=choice_id)
        context.user_data['choice'] = choice  # Store the choice in user_data

        # Ask the user to provide the new price
        await query.message.reply_text(MESSAGES[selected_lang]['enter_new_price'].format(choice.name))

        # Set state to collect the new price
        context.user_data['state'] = 'awaiting_edit_new_price_choice'

    except MenuItemChoices.DoesNotExist:
        await query.message.reply_text(MESSAGES[selected_lang]['choice_not_exist'])


async def edit_option_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    


    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['enter_new_option_title'])

    # Set state to awaiting title input
    context.user_data['state'] = 'awaiting_new_option_title'


async def handle_edit_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        

    if not selected_lang and account:
        selected_lang = account.language  # Use account language if selected_lang is missing
    
    await update.callback_query.answer()

    # Retrieve all contacts associated with the account
    contacts = await sync_to_async(list)(Contacts.objects.filter(account=account))

    keyboard = []

    # Loop through contacts to add buttons for each
    for contact in contacts:
        keyboard.append([InlineKeyboardButton(
            text=f"{contact.phone} / {contact.emails}",
            callback_data=f"edit_contact_{contact.id}"  # Callback to edit this contact
        )])

    # Option to create a new contact
    keyboard.append([InlineKeyboardButton(
        MESSAGES[selected_lang]['create_new_contact'],
        callback_data="create_new_contact"  # Callback to create a new contact
    )])

    keyboard.append([InlineKeyboardButton(MESSAGES[selected_lang]['delete_contact'], callback_data="delete_contact_list")],)


    keyboard.append([InlineKeyboardButton(MESSAGES[selected_lang]["buttons"]['cancel'], callback_data="cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['select_contact'], reply_markup=reply_markup)


async def edit_primary_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    account = context.user_data.get('account')

    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    await update.callback_query.answer()
    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['send_primary_color'])
    context.user_data['state'] = 'waiting_for_primary_color'


async def handle_primary_color_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    account = context.user_data.get('account')

    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    new_color = update.message.text
    
    if not new_color.startswith("#") or len(new_color) != 7:
        await update.message.reply_text(MESSAGES[selected_lang]['invalid_hex_format'])
        return

    account = context.user_data.get('account')
    if not account:
        chat_id = context.user_data.get('chat_id', update.message.chat.id)
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.message.reply_text(MESSAGES[selected_lang]['account_not_found'])
            return

    account.primary_color = new_color
    await sync_to_async(account.save)()
    await update.message.reply_text(MESSAGES[selected_lang]['primary_color_updated'].format(new_color=new_color))
    context.user_data['state'] = None


async def edit_secondary_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    account = context.user_data.get('account')

    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    await update.callback_query.answer()
    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['send_secondary_color'])
    context.user_data['state'] = 'waiting_for_secondary_color'


async def handle_secondary_color_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    account = context.user_data.get('account')

    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    new_color = update.message.text
    
    if not new_color.startswith("#") or len(new_color) != 7:
        await update.message.reply_text(MESSAGES[selected_lang]['invalid_hex_format'])
        return

    account = context.user_data.get('account')
    if not account:
        chat_id = context.user_data.get('chat_id', update.message.chat.id)
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.message.reply_text(MESSAGES[selected_lang]['account_not_found'])
            return

    account.second_color = new_color
    await sync_to_async(account.save)()
    await update.message.reply_text(MESSAGES[selected_lang]['secondary_color_updated'].format(new_color=new_color))
    context.user_data['state'] = None


async def edit_logo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    account = context.user_data.get('account')

    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    context.user_data['state'] = 'awaiting_edit_logo'
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['upload_logo'])


async def handle_edit_logo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    
    try:
        if not update.message.photo:
            await update.message.reply_text(MESSAGES[selected_lang]['upload_logo_image'])
            return

        logo_file = await update.message.photo[-1].get_file()
        logo_path = f"static/img/logos/{context.user_data.get('chat_id', update.message.chat.id)}_logo_{int(time.time())}.jpg"
        await logo_file.download_to_drive(logo_path)

        if 'account' not in context.user_data:
            chat_id = context.user_data.get('chat_id', update.message.chat.id)
            try:
                account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
                context.user_data['account'] = account
            except Account.DoesNotExist:
                await update.message.reply_text(MESSAGES[selected_lang]['account_not_found'])
                return
            
        account = context.user_data['account']

        if not selected_lang and account:
            selected_lang = account.language  # Replace with the actual field name for language in your Account model

        account.logo = logo_path
        await sync_to_async(account.save)()
        await update.message.reply_text(MESSAGES[selected_lang]['logo_updated'])

        context.user_data['state'] = None

    except Exception as e:
        await update.message.reply_text(f"{MESSAGES[selected_lang]['error_updating_logo']}: {str(e)}")


async def handle_title_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    try:
        new_title = update.message.text
        if 'account' not in context.user_data:
            chat_id = context.user_data.get('chat_id', update.message.chat.id)
            try:
                account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
                context.user_data['account'] = account
            except Account.DoesNotExist:
                await update.message.reply_text(MESSAGES[selected_lang]['account_not_found'])
                return

        account = context.user_data['account']
        if not selected_lang and account:
            selected_lang = account.language  # Replace with the actual field name for language in your Account model

        account.title = new_title
        await sync_to_async(account.save)()
        await update.message.reply_text(MESSAGES[selected_lang]['title_updated'].format(new_title=new_title))
        context.user_data['state'] = None

    except Exception as e:
        await update.message.reply_text(f"{MESSAGES[selected_lang]['error_updating_title']}: {str(e)}")


async def update_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    account = context.user_data.get('account')

    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    product = context.user_data.get('product')
    new_name = update.message.text
    product.item = new_name
    await sync_to_async(product.save)()

    # Update the product in context without deleting it
    context.user_data['product'] = product

    await update.message.reply_text(MESSAGES[selected_lang]['product_name_updated'].format(new_name=new_name))
    await show_start_message(update, context, account)
    # Clear the state without removing the product
    context.user_data.pop('state', None)



async def update_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    account = context.user_data.get('account')

    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    product = context.user_data.get('product')

    new_price = update.message.text

    # Update the product price
    product.price = new_price
    await sync_to_async(product.save)()

    # Send the success message
    await update.message.reply_text(MESSAGES[selected_lang]['price_updated'].format(new_price=new_price))
    await show_start_message(update, context, account)
    # Clean up user data
    context.user_data.pop('product', None)
    context.user_data.pop('state', None)

async def update_product_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = context.user_data.get('product_id')
    selected_lang = context.user_data.get('lang')
    account = context.user_data.get('account')
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    try:
        # Fetch product
        product = await sync_to_async(MenuItem.objects.get)(id=product_id)

        await update.message.reply_chat_action(action=ChatAction.UPLOAD_PHOTO)

        # Get the last photo file sent in the message and await get_file() correctly
        new_image = update.message.photo[-1]
        file = await new_image.get_file()  # Await here to get the actual File object

        # Download the photo to an in-memory byte stream
        image_stream = await file.download_as_bytearray()
        image_stream = io.BytesIO(image_stream)

        # Process the image using PIL
        with Image.open(image_stream) as img:
            # Compress the image and save it to a new BytesIO object
            compressed_image_stream = io.BytesIO()
            img.save(compressed_image_stream, format='JPEG', quality=85)
            compressed_image_stream.seek(0)  # Move to the start of the compressed image stream

            # Save the compressed image to file
            file_path = f'static/img/items/{product.item}_new_image.jpg'
            with open(file_path, 'wb') as f:
                f.write(compressed_image_stream.getvalue())

        # Update the product image path in the database
        product.picture = file_path
        await sync_to_async(product.save)()

        # Send success message
        await update.message.reply_text(MESSAGES[selected_lang]['product_image_updated'])

        await show_start_message(update, context, account)

    except MenuItem.DoesNotExist:
        await update.message.reply_text(MESSAGES[selected_lang]['product_not_found'])

    # Clean up user data in context
    context.user_data.pop('product_id', None)
    context.user_data.pop('state', None)


# Handle account username step
async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.replace('/', '')
    context.user_data['username'] = username

    # Retrieve the account to get the language preference
    chat_id = update.message.chat.id
    try:
        account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
        selected_lang = account.language if account.language else 'en'  # Default to English if no language is set

    except Exception as e:
        selected_lang = context.user_data.get('lang', 'en')

    # Send message in the user's selected language
    
    # Ask for the store logo in the user's selected language
    await update.message.reply_text(MESSAGES[selected_lang]['send_logo'])

    # Update the state for awaiting logo
    context.user_data['state'] = 'awaiting_logo'



# Handle account logo step
async def handle_logo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang', 'en')  # Default to 'en' if not set
    if not update.message.photo:
        await update.message.reply_text(MESSAGES[selected_lang]['photo_required'])
        return  # Exit the function if no photo is provided

    await update.message.reply_text(MESSAGES[selected_lang]['downloading_logo'])


    await update.message.reply_text(MESSAGES[selected_lang]['downloading_logo'])

    chat_id = context.user_data.get('chat_id', update.message.chat.id)
    context.user_data['chat_id'] = chat_id  # Cache chat ID

    try:
        # Get the highest resolution photo (last one in the list)
        logo_file = await update.message.photo[-1].get_file()

        # Ensure it's a valid image file
        if logo_file.file_path.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            logo_path = f"static/img/logos/{chat_id}_logo.jpg"
            await logo_file.download_to_drive(logo_path)

            await update.message.reply_text(MESSAGES[selected_lang]['logo_downloaded'])
            context.user_data['logo'] = logo_path
            await update.message.reply_text(MESSAGES[selected_lang]['ask_title'])
            context.user_data['state'] = 'awaiting_title'
        else:
            await update.message.reply_text(MESSAGES[selected_lang]['invalid_image_format'])

    except Exception as e:
        await update.message.reply_text(MESSAGES[selected_lang]['error_downloading_logo'].format(str(e)))


async def handle_cover_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')

    # Check if the update is a message or a callback query
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    account = context.user_data.get('account')
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        
    if account and account.language:
        selected_lang = account.language


    # Check if the state is set to 'awaiting_cover_upload'
    if context.user_data.get('state') != 'awaiting_cover_upload':
        await update.message.reply_text(MESSAGES[selected_lang]['invalid_upload'])
        return

    # Ensure an image is provided
    if not update.message.photo:
        await update.message.reply_text(MESSAGES[selected_lang]['no_image_upload'])
        return

    try:
        # Process the cover image (use the highest resolution photo)
        cover_file = await update.message.photo[-1].get_file()
        
        # Download the photo to an in-memory byte stream
        image_stream = await cover_file.download_as_bytearray()
        image_stream = io.BytesIO(image_stream)

        # Process the image using PIL
        with Image.open(image_stream) as img:
            # Compress the image and save it to a new BytesIO object
            compressed_image_stream = io.BytesIO()
            img.save(compressed_image_stream, format='JPEG', quality=85)
            compressed_image_stream.seek(0)  # Move to the start of the compressed image stream

            # Save the compressed image to a file
            cover_path = f"static/img/covers/{context.user_data.get('chat_id', update.message.chat.id)}_cover_{int(time.time())}.jpg"
            with open(cover_path, 'wb') as f:
                f.write(compressed_image_stream.getvalue())

        # Save the cover image to the Cover model
        account = context.user_data.get('account')
        if not account:
            chat_id = context.user_data.get('chat_id', update.message.chat.id)
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account

        cover = Cover(account=account, cover=cover_path)
        await sync_to_async(cover.save)()

        # Confirm the upload to the user
        await update.message.reply_text(MESSAGES[selected_lang]['cover_uploaded_successfully'])

        # Prompt the user to upload another cover photo with Yes/No buttons
        keyboard = [
            [
                InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['yes'], callback_data='upload_another_cover_yes'),
                InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['no'], callback_data='no_more_covers')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(MESSAGES[selected_lang]['upload_another_cover'], reply_markup=reply_markup)

    except Exception as e:
        # Log the exception if needed and inform the user of an error
        await update.message.reply_text(MESSAGES[selected_lang]['upload_error'])
        print(f"Error in handle_cover_upload: {e}")

    # Clear the state after upload
    context.user_data['state'] = None



async def upload_another_cover_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')

    account = context.user_data.get('account')
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    # Check if the update is from a message containing a photo
    if update.message and update.message.photo:
        await update.message.reply_text(MESSAGES[selected_lang]['cover_uploaded_successfully'])

        try:
            # Download the cover image
            cover_image_file = await update.message.photo[-1].get_file()
            cover_image_path = f"static/img/covers/{context.user_data.get('chat_id', update.message.chat.id)}_cover_{int(time.time())}.jpg"
            await cover_image_file.download_to_drive(cover_image_path)

            # Save the cover photo in the Cover model
            if account:
                # Create a new Cover instance
                cover = Cover(
                    account=account,
                    cover=cover_image_path  # Save the image path here
                )
                await sync_to_async(cover.save)()  # Save to the database asynchronously

                await update.message.reply_text(MESSAGES[selected_lang]['cover_downloaded_successfully'])

                # Ask if they want to upload another cover photo
                keyboard = [
                    [
                        InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['yes'], callback_data='upload_another_cover'),
                        InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['no'], callback_data='no_more_covers')
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(MESSAGES[selected_lang]['ask_upload_another_cover'], reply_markup=reply_markup)

            else:
                await update.message.reply_text(MESSAGES[selected_lang]['account_not_found'])

        except Exception as e:
            await update.message.reply_text(MESSAGES[selected_lang]['cover_download_error'].format(error=str(e)))

    elif update.callback_query:
        # Handle callback query for Yes/No buttons
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['cover_uploaded_successfully'])

    else:
        # Handle invalid input when no photo is provided
        await update.message.reply_text(MESSAGES[selected_lang]['invalid_image_type']) 
# Handle account title step
async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang', 'en')
    title = update.message.text
    context.user_data['title'] = title
    await update.message.reply_text(MESSAGES[selected_lang]['ask_phone_number'])
    context.user_data['state'] = 'awaiting_phone'


# Handle account phone number step
async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang', 'en')
    phone_number = update.message.text
    phone_number = phone_number.replace(" ", "")  # Remove spaces inside the number

    phone_pattern = r'^\+\d+$'

    if not re.match(phone_pattern, phone_number):
        await update.message.reply_text(MESSAGES[selected_lang]['invalid_phone_number'])
        return

    context.user_data['phone_number'] = phone_number

    try:
        user = await sync_to_async(User.objects.get)(id=1)
    except User.DoesNotExist:
        await update.message.reply_text(MESSAGES[selected_lang]['user_not_found'])
        return

    account_data = {
        'user': user,
        'username': context.user_data['username'],
        'logo': context.user_data['logo'],
        'title': context.user_data['title'],
        'phone_number': context.user_data['phone_number'],
        'telegramId': context.user_data['chat_id'],
        
    }

    if selected_lang:
        account_data['language'] = selected_lang

    if 'promoter' in context.user_data:
        account_data['promoter'] = context.user_data['promoter']

    if context.user_data.get('add_another_account'):
        account_data['owner'] = context.user_data.get('add_another_account')
        account_data['telegramId'] = ''
    new_account = Account(**account_data)
    try:
        await sync_to_async(new_account.save)()
        await update.message.reply_text(MESSAGES[selected_lang]['account_added_success'])

        #welcome_message = MESSAGES[selected_lang]['welcome_message']

        # Define the keyboard for user actions
        #buttons = MESSAGES[selected_lang]['buttons']
        #keyboard = [
        #    [
        #        InlineKeyboardButton(buttons['add_product'], callback_data="add_product"),
        #        InlineKeyboardButton(buttons['edit_product'], callback_data='edit_product')
        #    ],
        #    [
        #        InlineKeyboardButton(buttons['delete_product'], callback_data='delete_product')
        #    ],
        #    [
                #InlineKeyboardButton(buttons['delete_category'], callback_data="delete_category"),
        #        InlineKeyboardButton(buttons['edit_category'], callback_data="edit_category_menu"),
        #        InlineKeyboardButton(buttons['edit_store_info'], callback_data="edit_store_info")
        #    ],
        #    [
        #        InlineKeyboardButton(buttons['get_analytics'], callback_data="get_analytics") 
        #    ],
        #    [
        #        InlineKeyboardButton(buttons['get_website_qr'], callback_data="get_website_qr")
        #    ],
        #    [
        #        InlineKeyboardButton(buttons['help'], callback_data="help")  # New Help button
        #    ]
        #]

        #reply_markup = InlineKeyboardMarkup(keyboard)

        #await update.message.reply_text(
        #    welcome_message + MESSAGES[selected_lang]['commands_prompt'],
        #    reply_markup=reply_markup
        #)
        await show_start_message(update, context, new_account)

    except IntegrityError as e:
        print(e)

        await update.message.reply_text(MESSAGES[selected_lang]['username_taken'])
        await context.bot.send_message(chat_id="1281643104", text=str(e) + " " + str(phone_number))
        await start(update, context)  # Replace 'start' with your actual start function name

          # Clear user data to restart the process
        return



async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Determine the user's selected language
    selected_lang = context.user_data.get('lang')
    print("selected_lang in add_product")
    print(selected_lang)

    # Check if the update is a message or a callback query
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id  # Store chat ID in user_data

    # Fetch and cache account again to ensure it's available
    account = context.user_data.get('account')
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
        
    if account and account.language:
        selected_lang = account.language

    # Fetch existing categories for the account
    categories = await sync_to_async(list)(Category.objects.filter(account=account))  # Ensure ORM call is wrapped with sync_to_async

    # Create inline keyboard with existing categories and an option to add a new one
    keyboard = [[InlineKeyboardButton(category.name, callback_data=f"category_{category.name}")] for category in categories]
    keyboard.append([InlineKeyboardButton(MESSAGES[selected_lang]['create_new_category'], callback_data="create_new_category")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Now use the correct update object to reply with translated text
    if update.message:
        await update.message.reply_text(MESSAGES[selected_lang]['provide_category'], reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['provide_category'], reply_markup=reply_markup)

    context.user_data['state'] = 'awaiting_category'



# Handle product category step
async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message:
        category_name = update.message.text
    elif update.callback_query and context.user_data.get('category_name'):
        category_name = context.user_data['category_name']
    else:
        await update.callback_query.message.reply_text("Error: Unable to determine category name.")
        return

    account = context.user_data.get('account')

    # Get the user's selected language
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set

    # If the language is not set, check the account for the preferred language
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    try:
        category = await sync_to_async(Category.objects.get)(name=category_name, account=account)
        context.user_data['category'] = category

        if update.callback_query:
            await update.callback_query.message.reply_text(MESSAGES[selected_lang]['item_name_prompt'])
        else:
            await update.message.reply_text(MESSAGES[selected_lang]['item_name_prompt'])
        

        context.user_data['state'] = 'awaiting_item_name'

    except Category.DoesNotExist:
        context.user_data['category_name'] = category_name
        await handle_category_confirmation(update, context)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang')
    print("selected_lang")
    print(selected_lang)
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    # Check if the state is awaiting the user's input for contact phone
    if 'awaiting_contact' in context.user_data.get('state', ''):
        # User is expected to enter a phone number
        if update.message and update.message.text:
            # Remove spaces and validate the phone number
            phone_input = update.message.text.replace(" ", "").strip()
            
            # Regex to validate international phone number (e.g., +1234567890)
            phone_pattern = r"^\+?\d+$"
            
            if re.match(phone_pattern, phone_input):
                # Always create a new contact with the given phone number
                await sync_to_async(Contacts.objects.create)(
                    account=account,
                    phone=phone_input
                )

                # Clear the state and notify the user
                await update.message.reply_text(MESSAGES[selected_lang]['contact_added'])
                await show_start_message(update, context, account)
            else:
                await update.message.reply_text(MESSAGES[selected_lang]['invalid_phone'])
        else:
            await update.message.reply_text(MESSAGES[selected_lang]['invalid_phone'])
        return

    # If we're not awaiting a phone number, prompt the user to enter one
    await update.message.reply_text(MESSAGES[selected_lang]['enter_new_contacts'])
    context.user_data['state'] = 'awaiting_contact'


# Handle category creation confirmation
async def handle_category_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the user's selected language
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
    
    account = context.user_data.get('account')
    if not selected_lang and account:
        # Assuming the account model has a language field
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    category_name = context.user_data['category_name']
    keyboard = [
        [
            InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['yes'], callback_data="yes"),
            InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['no'], callback_data="no"),
            InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['cancel'], callback_data="cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Use the translated message for category confirmation

    if update.callback_query:
        await update.callback_query.message.reply_text(
            MESSAGES[selected_lang]['category_confirmation'].format(category_name=category_name),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            MESSAGES[selected_lang]['category_confirmation'].format(category_name=category_name),
            reply_markup=reply_markup
        )


async def handle_delete_cover_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang')

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    # Fetch covers associated with this account using sync_to_async
    covers = await sync_to_async(list)(Cover.objects.filter(account=account))
    if not covers:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['cover_not_found'])
        return

    # Loop through each cover and send it with a delete button
    for cover in covers:
        keyboard = [
            [InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['delete'], callback_data=f'delete_cover_{cover.id}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        with open(cover.cover.path, 'rb') as photo:
            await update.callback_query.message.reply_photo(photo=photo, reply_markup=reply_markup)


async def handle_add_options_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang')
    print("selected_lang")
    print(selected_lang)
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    
    # Ask for option title
    option_title_prompt = MESSAGES[selected_lang]['provide_option_title']
    await update.callback_query.message.reply_text(option_title_prompt)

    # Set state for collecting option title
    context.user_data['adding_option'] = True
    context.user_data['current_option'] = {'title': None, 'choices': []}
    context.user_data['state'] = 'awaiting_option_title'

async def handle_option_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = context.user_data.get('account')

    # Get the user's selected language
    selected_lang = context.user_data.get('lang')
    if not selected_lang and account:
        selected_lang = account.language

    chat_id = update.message.chat.id if update.message else update.callback_query.message.chat.id
    context.user_data['chat_id'] = chat_id

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return

    # Step 1: If user is entering option title
    if context.user_data.get('adding_option') or context.user_data.get('state') == "awaiting_new_option_name":
        option_title = update.message.text
        context.user_data['current_option'] = {'title': option_title, 'choices': [], 'prices': []}

        # Prompt for the first value
        option_values_prompt = MESSAGES[selected_lang]['provide_single_option_value']
        await update.message.reply_text(option_values_prompt)

        # Set state to collect the first option value
        context.user_data['collecting_value'] = True
        context.user_data['state'] = 'awaiting_single_option_value'

async def handle_option_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang')
    print("selected_lang")
    print(selected_lang)
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    if context.user_data.get('collecting_value'):
        # Get the value entered by the user
        option_value = update.message.text
        context.user_data['current_value'] = option_value  # Save current value

        # Ask for the price for this value
        option_price_prompt = MESSAGES[selected_lang]['provide_single_option_price'].format(value=option_value)

        await update.message.reply_text(option_price_prompt)

        # Set state for collecting the price for the current value
        context.user_data['collecting_price'] = True
        context.user_data['state'] = 'awaiting_single_option_price'

async def handle_option_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang')
    print("selected_lang")
    print(selected_lang)
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    if context.user_data.get('collecting_price'):
        # Get the price entered by the user
        option_price = update.message.text
        current_value = context.user_data['current_value']

        # Save the value and price
        context.user_data['current_option']['choices'].append(current_value)
        context.user_data['current_option']['prices'].append(option_price)
        #await store_option_in_db(context)
        print(context.user_data['current_option'])

        # Ask if the user wants to add another option
        more_option_values_prompt = MESSAGES[selected_lang]['add_more_option_values']

        more_options_keyboard = [
            [
                InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['yes'], callback_data="add_more_option_yes"),
                InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['no'], callback_data="add_more_option_no")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(more_options_keyboard)

        # Send the message with the button options
        await update.message.reply_text(
            more_option_values_prompt,
            reply_markup=reply_markup
        )

        # Reset state and wait for the user to click Yes or No
        context.user_data['collecting_value'] = False
        context.user_data['collecting_price'] = False
        context.user_data['state'] = 'awaiting_more_option_choice'

async def store_option_in_db(context):
    account = context.user_data.get('account')
    menu_item = context.user_data.get('menu_item')  # Assuming this holds the MenuItem object
    current_option = context.user_data.get('current_option')
    print("menu_item")
    print("current_option")
    print(menu_item)
    if menu_item == None:
        menu_item = context.user_data.get('product')
    print(current_option)
    # Create a new Option in the database
    option_title = current_option['title']

    new_option = await sync_to_async(Option.objects.create)(
        account=account,
        Item=menu_item,
        name=option_title,
        type='text',  # You can modify this to allow different types
        required=False
    )

    # Create MenuItemChoices for each choice with the corresponding price
    choices = current_option['choices']
    prices = current_option['prices']

    for choice, price in zip(choices, prices):
        await sync_to_async(MenuItemChoices.objects.create)(
            account=account,
            menuitem=menu_item,
            option=new_option,
            name=f"{choice}",
            price= price,
            Popular=False  # You can adjust the value for Popular based on additional logic
        )

    # Reset the current option in context for the next option, if any
    context.user_data['current_option'] = {'title': '', 'choices': [], 'prices': []}



async def delete_cover(cover_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang')
    print("selected_lang")
    print(selected_lang)
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    try:
        # Fetch the cover using sync_to_async
        cover = await sync_to_async(Cover.objects.get)(id=cover_id)
        cover_path = cover.cover.path

        # Delete the cover record in the database asynchronously
        await sync_to_async(cover.delete)()  # Wrap deletion in sync_to_async

        # Remove the file from the filesystem
        if os.path.exists(cover_path):
            os.remove(cover_path)

        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['cover_deleted'])
    except Cover.DoesNotExist:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['cover_not_found'])


async def show_social_media_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang')
    print("selected_lang")
    print(selected_lang)
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model


    if not account:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
        return

    await update.callback_query.answer()

    # Create the keyboard with social media options
    keyboard = [
        [InlineKeyboardButton(f"📘 Facebook", callback_data="edit_facebook")],
        [InlineKeyboardButton(f"📸 Instagram", callback_data="edit_instagram")],
        [InlineKeyboardButton(f"📱 WhatsApp", callback_data="edit_whatsapp")],
        [InlineKeyboardButton(f"🎵 TikTok", callback_data="edit_tiktok")],
        [InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['cancel'], callback_data="cancel")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['select_social_media'], reply_markup=reply_markup)


CURRENCIES = [
    ("Egyptian Pound", "EGP"),
    ("Saudi Riyal", "SAR"),
    ("UAE Dirham", "AED"),
    ("Syrian Pound", "SYP"),
    ("Kuwaiti Dinar", "KWD"),
    ("Qatari Riyal", "QAR"),
    ("Bahraini Dinar", "BHD"),
    ("Omani Rial", "OMR"),
    ("Libyan Dinar","LYD"),
    ("Moroccan Dirham", "MAD"),
    ("Tunisian Dinar", "TND"),
    ("Lebanese Pound", "LBP"),
    ("Jordanian Dinar", "JOD"),  
    ("Sudanese Pound", "SDG"),
    ("Algerian Dinar", "DZD"),
    ("Yemeni Rial", "YER"),
    ("Iraqi Dinar", "IQD"),
    ("US Dollar", "USD"),
    ("Euro", "EUR"),
    ("British Pound", "GBP"),
    ("Japanese Yen", "JPY"),
    ("Australian Dollar", "AUD"),
    ("Canadian Dollar", "CAD"),
    ("Swiss Franc", "CHF"),
    ("Chinese Yuan", "CNY"),
    ("Swedish Krona", "SEK"),
    ("New Zealand Dollar", "NZD"),
]
ITEMS_PER_PAGE = 5

async def show_currency_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0):
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang')
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model
    
    start_index = page * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    currencies = CURRENCIES[start_index:end_index]

    # Create buttons for the current page
    keyboard = [
        [InlineKeyboardButton(f"{name} ({code})", callback_data=f"currency_{code}")]
        for name, code in currencies
    ]

    # Add navigation buttons
    navigation_buttons = []
    if start_index > 0:  # Add "Previous" button
        navigation_buttons.append(InlineKeyboardButton(MESSAGES[selected_lang]['previous'], callback_data=f"currency_page_{page-1}"))
    if end_index < len(CURRENCIES):  # Add "Next" button
        navigation_buttons.append(InlineKeyboardButton(MESSAGES[selected_lang]['next'], callback_data=f"currency_page_{page+1}"))

    if navigation_buttons:
        keyboard.append(navigation_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.edit_text(
        text=MESSAGES[selected_lang]['select_currency'], reply_markup=reply_markup
    )


async def set_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang')
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model
    

    # Extract the selected currency code
    currency_code = query.data.split("_")[1]

    # Get the account from user data
    account = context.user_data.get('account')
    if not account:
        chat_id = query.message.chat.id
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return

    # Update the account currency
    account.currency = currency_code
    await sync_to_async(account.save)()

    # Send a confirmation message
    await query.answer()
    await query.message.reply_text(
        text=MESSAGES[selected_lang]['currency_updated'].format(currency=currency_code)
    )
    await show_start_message(update, context, account)
async def edit_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang')
    print("selected_lang")
    print(selected_lang)
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    query = update.callback_query
    await query.answer()

    # Extract address ID from callback data
    address_id = query.data.split("_")[2]  # Assuming format is "edit_address_<id>"

    # Fetch the address from the database
    try:
        address = await sync_to_async(Adresses.objects.get)(id=address_id)
        context.user_data['current_address'] = address  # Cache the address for editing

        await query.message.reply_text(MESSAGES[selected_lang]['enter_new_address'], reply_markup=None)
        context.user_data['state'] = 'awaiting_new_address'  # Set state for awaiting new address input

    except Adresses.DoesNotExist:
        await query.message.reply_text(MESSAGES[selected_lang]['address_not_found'])  # Error message if address not found

async def handle_category_selection(update, context):
    query = update.callback_query
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang')

    print("selected_lang")
    print(selected_lang)
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    if not account:
        try:
            # Use sync_to_async to fetch account from the database
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            no_account_msg = MESSAGES[selected_lang]['no_account']
            if update.message:
                await update.message.reply_text(no_account_msg)
            elif update.callback_query:
                await update.callback_query.message.reply_text(no_account_msg)
            return
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    # Extract category ID from the callback data
    category_id = int(query.data.split("_")[-1])
    context.user_data['category_id_to_edit'] = category_id  # Store the category ID to use later

    # Prompt the user to enter a new name
    await query.message.reply_text(
        MESSAGES[selected_lang]['enter_new_category_name']
    )
    

async def handle_category_picture_edit(update, context):
    query = update.callback_query
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang') 

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id

    if not account:
        try:
            # Use sync_to_async to fetch account from the database
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            no_account_msg = MESSAGES[selected_lang]['no_account']
            if update.message:
                await update.message.reply_text(no_account_msg)
            elif update.callback_query:
                await update.callback_query.message.reply_text(no_account_msg)
            return

    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    # Extract category ID from the callback data
    category_id = int(query.data.split("_")[-1])
    context.user_data['category_id_to_edit'] = category_id  # Store the category ID to use later
    context.user_data['state'] = "awaiting_new_category_picture"
    # Prompt the user to upload a new picture
    await query.message.reply_text(
        MESSAGES[selected_lang]['upload_new_category_picture']
    )

async def handle_edit_category_menu(update, context, selected_lang):
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang')

    print("selected_lang")
    print(selected_lang)
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    if not account:
        try:
            # Use sync_to_async to fetch account from the database
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            no_account_msg = MESSAGES[selected_lang]['no_account']
            if update.message:
                await update.message.reply_text(no_account_msg)
            elif update.callback_query:
                await update.callback_query.message.reply_text(no_account_msg)
            return
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    # Fetch categories asynchronously
    categories = await sync_to_async(list)(Category.objects.filter(account=account))

    # Create buttons for each category
    category_buttons = [
        [InlineKeyboardButton(category.name, callback_data=f"edit_category_{category.id}")]
        for category in categories
    ]

    category_reply_markup = InlineKeyboardMarkup(category_buttons)

    # Send the list of categories to the user
    await update.callback_query.message.reply_text(
        MESSAGES[selected_lang]['choose_category_to_edit'],
        reply_markup=category_reply_markup
    )

async def handle_add_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang') 

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id

    if not account:
        try:
            # Use sync_to_async to fetch account from the database
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            no_account_msg = MESSAGES[selected_lang]['no_account']
            if update.message:
                await update.message.reply_text(no_account_msg)
            elif update.callback_query:
                await update.callback_query.message.reply_text(no_account_msg)
            return

    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model


    context.user_data['adding_coupon'] = {"step": "code"}  # Start the coupon creation process
    context.user_data['state'] = "enter_coupon_code"
    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['enter_coupon_code'])


async def handle_remove_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang') 

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id

    if not account:
        try:
            # Use sync_to_async to fetch account from the database
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            no_account_msg = MESSAGES[selected_lang]['no_account']
            if update.message:
                await update.message.reply_text(no_account_msg)
            elif update.callback_query:
                await update.callback_query.message.reply_text(no_account_msg)
            return

    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    # Retrieve coupons associated with the account
    coupons = await sync_to_async(list)(CouponCode.objects.filter(account=account))

    if not coupons:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_coupons'])
        return

    # Create buttons for each coupon
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"{coupon.code} - {coupon.amount}",
                callback_data=f"remove_coupon_{coupon.id}"
            )
        ]
        for coupon in coupons
    ]

    # Add a cancel button
    keyboard.append([InlineKeyboardButton(MESSAGES[selected_lang]['cancel'], callback_data="cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['select_coupon_to_remove'], reply_markup=reply_markup)


async def handle_coupon_removal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang') 

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id

    if not account:
        try:
            # Use sync_to_async to fetch account from the database
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            no_account_msg = MESSAGES[selected_lang]['no_account']
            if update.message:
                await update.message.reply_text(no_account_msg)
            elif update.callback_query:
                await update.callback_query.message.reply_text(no_account_msg)
            return

    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    query = update.callback_query
    await query.answer()  # Acknowledge the callback query

    # Extract the coupon ID from the callback data
    data = query.data
    coupon_id = data.split("_")[-1]

    try:
        # Remove the coupon
        coupon = await sync_to_async(CouponCode.objects.get)(id=coupon_id)
        await sync_to_async(coupon.delete)()
        await query.message.reply_text(MESSAGES[selected_lang]['coupon_removed'])
    except CouponCode.DoesNotExist:
        await query.message.reply_text(MESSAGES[selected_lang]['coupon_not_found'])


async def confirm_delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang')

    print("selected_lang")
    print(selected_lang)
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    query = update.callback_query
    category_id = query.data.split("_")[-1]  # Extract the category ID from the callback data

    # Store the category ID in context for final deletion
    context.user_data['category_id_to_delete'] = category_id

    # Ask for confirmation
    confirm_keyboard = [
        [
            InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['yes'], callback_data="confirm_delete_yes"),
            InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['no'], callback_data="cancel")
        ]
    ]
    confirm_reply_markup = InlineKeyboardMarkup(confirm_keyboard)

    await query.answer()  # Acknowledge the callback
    await query.message.reply_text(
        MESSAGES[selected_lang]['confirm_delete_message'],
        reply_markup=confirm_reply_markup
    )

async def show_address_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = context.user_data.get('account')

    # Get the user's selected language, defaulting to 'en' if not set
    selected_lang = context.user_data.get('lang')

    print("selected_lang")
    print(selected_lang)
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model


    # Retrieve all addresses associated with the account
    addresses = await sync_to_async(list)(Adresses.objects.filter(account=account))

    keyboard = []

    # Loop through addresses to add buttons for each
    for address in addresses:
        keyboard.append([InlineKeyboardButton(
            text=f"{address.address}",
            callback_data=f"edit_address_{address.id}"  # Callback to edit this address
        )])

    # Option to create a new address
    keyboard.append([InlineKeyboardButton(
        MESSAGES[selected_lang]['create_new_address'],
        callback_data="create_new_address"  # Callback to create a new address
    )])

    keyboard.append([InlineKeyboardButton(MESSAGES[selected_lang]['delete_address'], callback_data="delete_address_list")],)

    keyboard.append([InlineKeyboardButton(MESSAGES[selected_lang]['cancel'], callback_data="cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['select_address'], reply_markup=reply_markup)


async def start_creating_address(update: Update, context: ContextTypes.DEFAULT_TYPE):

    selected_lang = context.user_data.get('lang')
    account = context.user_data.get('account')
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model


    if 'state' in context.user_data and context.user_data['state'] == 'awaiting_address_details':
        address_details = update.message.text  # Get the address input from the user

        # Save the new address to the database
        new_address = Adresses(account=account, address=address_details)  # Assuming Address model has 'details' field
        await sync_to_async(new_address.save)()  # Save to the database

        await update.message.reply_text(MESSAGES[selected_lang]['address_added'])  # Confirm addition
        await show_start_message(update, context, account)

    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unexpected_input'])  # Handle unexpected input

async def handle_new_category_name(update, context):
    selected_lang = context.user_data.get('lang')
    account = context.user_data.get('account')
    
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    if not account:
        try:
            # Use sync_to_async to fetch account from the database
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            no_account_msg = MESSAGES[selected_lang]['no_account']
            if update.message:
                await update.message.reply_text(no_account_msg)
            elif update.callback_query:
                await update.callback_query.message.reply_text(no_account_msg)
            return
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    new_name = update.message.text  # Get the new name from the user's message
    category_id = context.user_data.get('category_id_to_edit')

    # Retrieve and update the category asynchronously
    try:
        category = await sync_to_async(Category.objects.get)(id=category_id)
        category.name = new_name
        await sync_to_async(category.save)()  # Save the updated category asynchronously

        # Confirm the update
        await update.message.reply_text(MESSAGES[selected_lang]['category_updated_successfully'])
        await show_start_message(update, context, account)
    except Category.DoesNotExist:
        await update.message.reply_text(MESSAGES[selected_lang]['category_not_found'])


async def show_delete_contact_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    account = context.user_data.get('account')
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
            context.user_data['account'] = account  # Cache the account for future use
        except Account.DoesNotExist:
            if update.message:
                await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
            elif update.callback_query:
                await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
            return
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model


    # Retrieve all contacts associated with the account
    contacts = await sync_to_async(list)(Contacts.objects.filter(account=account))

    keyboard = []

    # Loop through contacts to add buttons for each
    for contact in contacts:
        keyboard.append([InlineKeyboardButton(
            text=f"{contact.phone} / {contact.emails}",
            callback_data=f"confirm_delete_contact_{contact.id}"  # Callback to confirm delete
        )])

    keyboard.append([InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['cancel'], callback_data="cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['select_contact_to_delete'], reply_markup=reply_markup)


async def show_address_list_for_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = context.user_data.get('account')
    selected_lang = context.user_data.get('lang', 'en')

    # Ensure the chat_id is set
    chat_id = update.callback_query.message.chat.id

    # Retrieve all addresses associated with the account
    addresses = await sync_to_async(list)(Adresses.objects.filter(account=account))

    keyboard = []

    # Loop through addresses to add buttons for each address with delete option
    for address in addresses:
        keyboard.append([InlineKeyboardButton(
            text=f"🗑️ Delete {address.address}",
            callback_data=f"delete_address_{address.id}"  # Callback to delete this address
        )])

    keyboard.append([InlineKeyboardButton(MESSAGES[selected_lang]['cancel'], callback_data="cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['select_address_to_delete'], reply_markup=reply_markup)


async def show_categories_for_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
    chat_id = update.callback_query.message.chat.id
    account = context.user_data.get('account')

    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account_found'])
            return

    if not selected_lang and account:
        selected_lang = account.language

    # Fetch categories related to the account asynchronously
    categories = await sync_to_async(list)(Category.objects.filter(account=account))

    if not categories:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_categories_available'])
        return

    # Create InlineKeyboard with category names as options
    keyboard = [
        [InlineKeyboardButton(category.name, callback_data=f"confirm_delete_category_{category.id}")]
        for category in categories
    ]
    keyboard.append([InlineKeyboardButton(MESSAGES[selected_lang]['cancel'], callback_data="cancel")])  # Add a cancel button
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(
        MESSAGES[selected_lang]['select_category_to_delete'],
        reply_markup=reply_markup
    )

async def confirm_delete_contact(update: Update, context: ContextTypes.DEFAULT_TYPE, contact_id):
    selected_lang = context.user_data.get('lang')
    chat_id = update.callback_query.message.chat.id
    account = context.user_data.get('account')

    if not account:
        # Try to retrieve the account again in case it's not in user_data
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account_found'])
            return
    if not selected_lang and account:
        # Assuming the account model has a language field
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    # Retrieve the contact that the user wants to delete
    try:
        contact = await sync_to_async(Contacts.objects.get)(id=contact_id)
        context.user_data['contact_to_delete'] = contact_id  # Store the contact ID for deletion confirmation

        # Ask the user for confirmation before deleting
        keyboard = [
            [InlineKeyboardButton(MESSAGES[selected_lang]['confirm'], callback_data="delete_contact_confirm")],
            [InlineKeyboardButton(MESSAGES[selected_lang]['cancel'], callback_data="cancel")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['confirm_contact_delete'], reply_markup=reply_markup)
    
    except Contacts.DoesNotExist:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['contact_not_found'])

async def delete_selected_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    contact_id = context.user_data.get('contact_to_delete')
    chat_id = update.callback_query.message.chat.id
    account = context.user_data.get('account')

    if not account:
        # Try to retrieve the account again in case it's not in user_data
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account_found'])
            return
    if not selected_lang and account:
        # Assuming the account model has a language field
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    try:
        # Retrieve and delete the contact
        contact = await sync_to_async(Contacts.objects.get)(id=contact_id)
        await sync_to_async(contact.delete)()

        # Notify the user that the contact was deleted
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['contact_deleted'])

        # Optionally reload the contacts list
        await handle_edit_contacts(update, context)
    
    except Contacts.DoesNotExist:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['contact_not_found'])


async def delete_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    selected_lang = context.user_data.get('lang')
    chat_id = update.callback_query.message.chat.id
    account = context.user_data.get('account')

    if not account:
        # Try to retrieve the account again in case it's not in user_data
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account_found'])
            return
    if not selected_lang and account:
        # Assuming the account model has a language field
        selected_lang = account.language  # Replace with the actual field name for language in your Account model


    # Acknowledge the callback query
    await query.answer()

    address_id = int(query.data.split("_")[-1])  # Get the address ID from callback data

    try:
        # Retrieve and delete the address
        address = await sync_to_async(Adresses.objects.get)(id=address_id, account=context.user_data['account'])
        await sync_to_async(address.delete)()  # Delete the address

        await query.message.reply_text(MESSAGES[selected_lang]['address_deleted'])  # Confirm deletion
        await show_start_message(update, context, account)
    except Adresses.DoesNotExist:
        await query.message.reply_text(MESSAGES[selected_lang]['address_not_found'])


async def delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    #category_id = query.data.split("_")[2]  # Extract the category ID from the callback data
    category_id = context.user_data.get('category_id_to_delete')
    # Fetch the language from context or account
    selected_lang = context.user_data.get('lang')
    chat_id = update.callback_query.message.chat.id
    account = context.user_data.get('account')

    if not account:
        # Try to retrieve the account again in case it's not in user_data
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account_found'])
            return
    if not selected_lang and account:
        # Assuming the account model has a language field
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    try:
        category = await sync_to_async(Category.objects.get)(id=category_id)
        category_name = category.name
        await sync_to_async(category.delete)()  # Delete the category

        # Send the success message with translation
        await query.message.reply_text(
            MESSAGES[selected_lang]['category_deleted'].format(category_name=category_name)
        )
        await show_start_message(update, context, account)
    except Exception as e:
        # Send the error message with translation
        await query.message.reply_text(
            MESSAGES[selected_lang]['category_delete_error'].format(error_message=str(e))
        )
async def edit_instagram_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    chat_id = update.message.chat.id
    account = context.user_data.get('account')

    if not account:
        # Try to retrieve the account again in case it's not in user_data
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account_found'])
            return
            
    if not selected_lang and account:
        # Assuming the account model has a language field
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    # Check if the state is set to awaiting_instagram_link
    if context.user_data.get('state') == 'awaiting_instagram_link':
        new_instagram_link = update.message.text  # Get the new Instagram link from the message
        
        # Validate the link format
        valid_prefixes = [
            "instagram.com",
            "https://www.instagram.com/",
            "www.instagram.com"
        ]
        if not any(new_instagram_link.startswith(prefix) for prefix in valid_prefixes):
            await update.message.reply_text(MESSAGES[selected_lang]['invalid_instagram_link'])
            return
        
        # Retrieve the account from user data
        account = context.user_data.get('account')
        
        if account:
            # Update the Instagram link in the database
            social_media_instance, created = await sync_to_async(SocialMedia.objects.get_or_create)(account=account)
            social_media_instance.instagram = new_instagram_link
            await sync_to_async(social_media_instance.save)()  # Save the updated instance
            
            await update.message.reply_text(MESSAGES[selected_lang]['social_media_instagram_updated'])
            await show_start_message(update, context, account)
        else:
            await update.message.reply_text(MESSAGES[selected_lang]['no_social_media'])
        
        # Reset the state
        context.user_data['state'] = None
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['no_social_media'])

async def edit_whatsapp_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    chat_id = update.message.chat.id
    account = context.user_data.get('account')

    if not account:
        # Try to retrieve the account again in case it's not in user_data
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.message.reply_text(MESSAGES[selected_lang]['no_account_found'])
            return

    if not selected_lang and account:
        # Assuming the account model has a language field
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    # Check if the state is set to awaiting_whatsapp_link
    if context.user_data.get('state') == 'awaiting_whatsapp_link':
        new_whatsapp_link = update.message.text  # Get the new WhatsApp link from the message
        
        # Validate the link format
        valid_prefixes = [
            "wa.me/"
        ]
        if not any(new_whatsapp_link.startswith(prefix) for prefix in valid_prefixes):
            await update.message.reply_text(MESSAGES[selected_lang]['invalid_whatsapp_link'])
            return
        
        # Retrieve the account from user data
        account = context.user_data.get('account')
        
        if account:
            # Update the WhatsApp link in the database
            social_media_instance, created = await sync_to_async(SocialMedia.objects.get_or_create)(account=account)
            social_media_instance.whatsapp = new_whatsapp_link  # Change to the WhatsApp field
            await sync_to_async(social_media_instance.save)()  # Save the updated instance
            
            await update.message.reply_text(MESSAGES[selected_lang]['social_media_whatsapp_updated'])
            await show_start_message(update, context, account)

        else:
            await update.message.reply_text(MESSAGES[selected_lang]['no_social_media'])
        
        # Reset the state
        context.user_data['state'] = None
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['no_social_media'])

async def edit_tiktok_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    chat_id = update.message.chat.id
    account = context.user_data.get('account')

    if not account:
        # Try to retrieve the account again in case it's not in user_data
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.message.reply_text(MESSAGES[selected_lang]['no_account_found'])
            return

    if not selected_lang and account:
        # Assuming the account model has a language field
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    # Check if the state is set to awaiting_tiktok_link
    if context.user_data.get('state') == 'awaiting_tiktok_link':
        new_tiktok_link = update.message.text  # Get the new TikTok link from the message
        
        # Validate the link format
        valid_prefixes = [
            "tiktok.com",
            "https://www.tiktok.com/",
            "www.tiktok.com"
        ]
        if not any(new_tiktok_link.startswith(prefix) for prefix in valid_prefixes):
            await update.message.reply_text(MESSAGES[selected_lang]['invalid_tiktok_link'])
            return
        
        # Retrieve the account from user data
        account = context.user_data.get('account')
        
        if account:
            # Update the TikTok link in the database
            social_media_instance, created = await sync_to_async(SocialMedia.objects.get_or_create)(account=account)
            social_media_instance.tiktok = new_tiktok_link  # Change to the TikTok field
            await sync_to_async(social_media_instance.save)()  # Save the updated instance
            
            await update.message.reply_text(MESSAGES[selected_lang]['social_media_tiktok_updated'])
            await show_start_message(update, context, account)

        else:
            await update.message.reply_text(MESSAGES[selected_lang]['no_social_media'])
        
        # Reset the state
        context.user_data['state'] = None
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['no_social_media'])

async def edit_facebook_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    chat_id = update.message.chat.id
    account = context.user_data.get('account')

    if not account:
        # Try to retrieve the account again in case it's not in user_data
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.message.reply_text(MESSAGES[selected_lang]['no_account_found'])
            return
            
    if not selected_lang and account:
        # Assuming the account model has a language field
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    # Check if the state is set to awaiting_facebook_link
    if context.user_data.get('state') == 'awaiting_facebook_link':
        new_facebook_link = update.message.text  # Get the new Facebook link from the message
        
        # Validate the link format
        valid_prefixes = [
            "facebook.com",
            "www.facebook.com",
            "https://www.facebook.com"
        ]
        if not any(new_facebook_link.startswith(prefix) for prefix in valid_prefixes):
            await update.message.reply_text(MESSAGES[selected_lang]['invalid_facebook_link'])
            return
        
        # Retrieve the account from user data
        account = context.user_data.get('account')
        
        if account:
            # Update the Facebook link in the database
            social_media_instance, created = await sync_to_async(SocialMedia.objects.get_or_create)(account=account)
            social_media_instance.facebook = new_facebook_link
            await sync_to_async(social_media_instance.save)()  # Save the updated instance
            
            await update.message.reply_text(MESSAGES[selected_lang]['social_media_facebook_updated'])
            await show_start_message(update, context, account)
        else:
            await update.message.reply_text(MESSAGES[selected_lang]['no_social_media'])
        
        # Reset the state
        context.user_data['state'] = None
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['no_social_media'])



async def process_coupon_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    chat_id = update.message.chat.id
    account = context.user_data.get('account')

    if not account:
        # Try to retrieve the account again in case it's not in user_data
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.message.reply_text(MESSAGES[selected_lang]['no_account_found'])
            return
            
    if not selected_lang and account:
        # Assuming the account model has a language field
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    user_data = context.user_data.get('adding_coupon', {})
    if user_data.get('step') != "code":
        return  # Not in the process of adding a coupon

    coupon_code = update.message.text.strip()
    user_data["code"] = coupon_code  # Save the coupon code
    user_data["step"] = "amount"  # Move to the next step

    print("inside process_coupon_code")
    await update.message.reply_text(MESSAGES[selected_lang]['enter_coupon_amount'])
    context.user_data['state'] = 'enter_coupon_amount'


async def process_coupon_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')
    chat_id = update.message.chat.id
    account = context.user_data.get('account')

    if not account:
        # Try to retrieve the account again in case it's not in user_data
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.message.reply_text(MESSAGES[selected_lang]['no_account_found'])
            return
            
    if not selected_lang and account:
        # Assuming the account model has a language field
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    user_data = context.user_data.get('adding_coupon', {})
    print("wewewewewe")
    if user_data.get('step') != "amount":
        print("weweewewwwwww")
        return  # Not in the process of adding a coupon

    try:
        coupon_amount = float(update.message.text.strip())  # Ensure the amount is valid
    except ValueError:
        await update.message.reply_text(MESSAGES[selected_lang]['invalid_amount'])
        return

    user_data["amount"] = coupon_amount

    # Retrieve account and save the coupon
    account = context.user_data.get('account')
    if not account:
        await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
        return

    try:
        await sync_to_async(CouponCode.objects.create)(
            account=account,
            code=user_data["code"],
            amount=user_data["amount"]
        )
        await update.message.reply_text(MESSAGES[selected_lang]['coupon_added'])
    except Exception as e:
        await update.message.reply_text(f"Error saving coupon: {str(e)}")
    finally:
        context.user_data.pop('adding_coupon', None)  # Clear the process

# Handle item name step
async def handle_item_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    item_name = update.message.text
    context.user_data['item_name'] = item_name

    # Get the user's selected language
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set

    # If the language is not set, check the account for the preferred language
    account = context.user_data.get('account')
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    await update.message.reply_text(MESSAGES[selected_lang]['item_price_prompt'])
    context.user_data['state'] = 'awaiting_price'

async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the user's selected language
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
    account = context.user_data.get('account')
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    price = update.message.text

    if not price.isdigit():
        await update.message.reply_text(MESSAGES[selected_lang]['invalid_price'])
        return

    context.user_data['price'] = int(price)
    await update.message.reply_text(MESSAGES[selected_lang]['awaiting_description'])
    context.user_data['state'] = 'awaiting_description'

async def start_editing_address(update: Update, context: ContextTypes.DEFAULT_TYPE, address_id):
    selected_lang = context.user_data.get('lang')

    # Fetch the selected address
    address = await sync_to_async(Adresses.objects.get)(id=address_id)
    context.user_data['address_to_edit'] = address_id  # Store the address ID for later use

    await update.callback_query.message.reply_text(f"{MESSAGES[selected_lang]['editing_address']}: {address.street}, {address.city}, {address.country}")
    context.user_data['state'] = 'awaiting_address_edit'


async def handle_contact_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    selected_lang = context.user_data.get('lang')
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    account = context.user_data.get('account')

    if not account:
        # Try to retrieve the account again in case it's not in user_data
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account_found'])
            return
        
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model


    if state == 'awaiting_new_contact':
        contact = context.user_data.get('contact')

        # Validate if the input is a valid phone number
        if update.message.text.isdigit():
            contact.phone = int(update.message.text)
            await sync_to_async(contact.save)()  # Save the updated contact
            await update.message.reply_text(MESSAGES[selected_lang]['contact_updated'])
            await show_start_message(update, context, account)
        else:
            await update.message.reply_text(MESSAGES[selected_lang]['invalid_phone'])


async def handle_new_address_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    selected_lang = context.user_data.get('lang')
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    account = context.user_data.get('account')

    if not account:
        # Try to retrieve the account again in case it's not in user_data
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account_found'])
            return
        
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model


    if 'state' in context.user_data and context.user_data['state'] == 'awaiting_new_address':
        new_address_text = update.message.text  # Get the new address input from the user
        
        # Update the current address with the new details
        current_address = context.user_data.get('current_address')
        if current_address:
            current_address.address = new_address_text  # Assuming 'address' is the field name in your model
            await sync_to_async(current_address.save)()  # Save the updated address
            
            await update.message.reply_text(MESSAGES[selected_lang]['address_updated'])  # Confirm update
            await show_start_message(update, context, account)
        else:
            await update.message.reply_text(MESSAGES[selected_lang]['address_not_found'])  # Handle case where address is not found

    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unexpected_input'])  # Handle unexpected input



async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the user's selected language
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set

    account = context.user_data.get('account')
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model


    description = update.message.text
    context.user_data['description'] = description  # Store the description for the next step
    
    # Use the translated message for asking for the product image
    await update.message.reply_text(MESSAGES[selected_lang]['awaiting_image'])
    context.user_data['state'] = 'awaiting_image'

async def upload_another_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set

    account = context.user_data.get('account')
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    # Check if the update is from a message containing a photo
    if update.message and update.message.photo:
        await update.message.reply_text(MESSAGES[selected_lang]['downloading_image'])

        try:
            # Download the product image
            product_image_file = await update.message.photo[-1].get_file()
            product_image_path = f"static/img/items/{context.user_data.get('chat_id', update.message.chat.id)}_product_{int(time.time())}.jpg"
            await product_image_file.download_to_drive(product_image_path)

            # Save the photo in the MenuItemPhoto model
            menuitem_id = context.user_data.get('menuitem_id')  # Get the menu item ID from user data

            # Ensure that the MenuItem ID exists in the context
            if menuitem_id:
                # Create a new MenuItemPhoto instance
                menu_item_photo = MenuItemPhoto(
                    account=account,
                    menuitem_id=menuitem_id,
                    picture=product_image_path  # Save the image path here
                )
                await sync_to_async(menu_item_photo.save)()  # Save to the database asynchronously

                await update.message.reply_text(MESSAGES[selected_lang]['image_downloaded_successfully'])

                # Ask if they want to upload another photo
                keyboard = [
                    [
                        InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['yes'], callback_data='upload_another_photo'),
                        InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['no'], callback_data='no_more_photos')
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(MESSAGES[selected_lang]['ask_upload_another_photo'], reply_markup=reply_markup)

            else:
                await update.message.reply_text(MESSAGES[selected_lang]['menuitem_id_missing'])

        except Exception as e:
            await update.message.reply_text(MESSAGES[selected_lang]['image_download_error'].format(error=str(e)))

    elif update.callback_query:
        # Handle callback query for Yes/No buttons
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['downloading_image'])

    else:
        # Handle invalid input when no photo is provided
        await update.message.reply_text(MESSAGES[selected_lang]['invalid_image_type'])



async def no_more_covers(update:Update, context:ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
    account = context.user_data.get('account')

    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    await show_start_message(update, context, account)
    
async def no_more_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
    account = context.user_data.get('account')

    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    menuitem = context.user_data.get('menu_item')
    username = account.username  # Get the username from the cached account
    print("menuitem")
    print(menuitem)
    website_url = f"tidy-taps.com/f/{quote(username)}"
    
    if update.callback_query:
        await update.callback_query.answer()  # Acknowledge the callback
        await update.callback_query.message.reply_text(
            f"🎉 {MESSAGES[selected_lang]['product_added_successfully'].format(item=menuitem.item)}\n"
            f"{MESSAGES[selected_lang]['visit_product_page'].format(url=website_url)}"
        )
    elif update.message:
        await update.message.reply_text(
            f"🎉 {MESSAGES[selected_lang]['product_added_successfully'].format(item=menuitem.item)}\n"
            f"{MESSAGES[selected_lang]['visit_product_page'].format(url=website_url)}"
        )

    add_options_prompt = MESSAGES[selected_lang]['do_you_want_to_add_options']

    options_keyboard = [
        [
            InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['yes'], callback_data="add_options_yes"),
            InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['no'], callback_data="add_options_no")
        ]
    ]

    options_reply_markup = InlineKeyboardMarkup(options_keyboard)

    if update.callback_query:
        await update.callback_query.message.reply_text(
            add_options_prompt,
            reply_markup=options_reply_markup
        )
    elif update.message:
        await update.message.reply_text(
            add_options_prompt,
            reply_markup=options_reply_markup
        )


async def handle_product_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the user's selected language
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
    account = context.user_data.get('account')
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model
    if not update.message.photo:
        await update.message.reply_text(MESSAGES[selected_lang]['invalid_image_type'])
        return
    await update.message.reply_text(MESSAGES[selected_lang]['downloading_image'])

    try:
        # Download the product image
        product_image_file = await update.message.photo[-1].get_file()
        product_image_path = f"static/img/items/{context.user_data.get('chat_id', update.message.chat.id)}_product_{int(time.time())}.jpg"
        await product_image_file.download_to_drive(product_image_path)
        await update.message.reply_text(MESSAGES[selected_lang]['image_downloaded_successfully'])

        # Save the menu item with all the information
        account = context.user_data['account']
        if not account:
            try:
                chat_id = context.user_data.get('chat_id', update.message.chat.id)
                account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
                context.user_data['account'] = account  # Cache the account for future use
            except Account.DoesNotExist:
                await update.message.reply_text(MESSAGES[selected_lang]['create_account_first'])
                return
        
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
        context.user_data['menuitem_id'] = menu_item.id 
        context.user_data['menu_item'] = menu_item
        # Get the website URL for the account
        

        # Send the success message with the website link
        keyboard = [
            [
                InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['yes'], callback_data='upload_another_photo'),
                InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['no'], callback_data='no_more_photos')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(MESSAGES[selected_lang]['ask_upload_another_photo'], reply_markup=reply_markup)
        

    except Exception as e:
        print(e)
        await update.message.reply_text(MESSAGES[selected_lang]['image_download_error'].format(error=str(e)))

async def handle_uploaded_picture(update, context):
    """
    Handle uploaded category picture, download it, and update the category in the database.
    """
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
    account = context.user_data.get('account')
    
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    # Validate the uploaded photo
    if not update.message.photo:
        await update.message.reply_text(MESSAGES[selected_lang]['invalid_image_type'])
        return

    await update.message.reply_text(MESSAGES[selected_lang]['downloading_category_image'])

    try:
        # Download the category image
        category_image_file = await update.message.photo[-1].get_file()
        category_image_path = f"static/img/category/{context.user_data.get('chat_id', update.message.chat.id)}_category_{int(time.time())}.jpg"
        await category_image_file.download_to_drive(category_image_path)
        await update.message.reply_text(MESSAGES[selected_lang]['category_image_downloaded_successfully'])

        # Retrieve account information
        account = context.user_data.get('account')
        if not account:
            try:
                chat_id = context.user_data.get('chat_id', update.message.chat.id)
                account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
                context.user_data['account'] = account  # Cache the account for future use
            except Account.DoesNotExist:
                await update.message.reply_text(MESSAGES[selected_lang]['create_account_first'])
                return

        # Get the category to update
        category_id = context.user_data.get('category_id_to_edit')
        if not category_id:
            await update.message.reply_text(MESSAGES[selected_lang]['no_category_selected'])
            return

        # Update the category's image field
        category = await sync_to_async(Category.objects.get)(id=category_id)
        await sync_to_async(setattr)(category, 'picture', category_image_path)
        await sync_to_async(category.save)()

        # Notify the user of successful update
        await update.message.reply_text(MESSAGES[selected_lang]['category_picture_updated'])
        await show_start_message(update, context, account)

    except Exception as e:
        # Log error for debugging (replace with proper logging in production)
        print(f"Error in handle_uploaded_picture: {e}")
        await update.message.reply_text(MESSAGES[selected_lang]['upload_failed'])

async def show_products_for_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang',)  # Default to 'en' if language is not set
    
    try:
        account = context.user_data.get('account')
        if not account:
            try:
                if update.message:
                    chat_id = context.user_data.get('chat_id', update.message.chat.id)
                elif update.callback_query:
                    chat_id = context.user_data.get('chat_id', update.callback_query.message.chat.id)

                account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
                context.user_data['account'] = account  # Cache the account for future use
            except Account.DoesNotExist:
                if update.message:
                    await update.message.reply_text(MESSAGES[selected_lang]['create_account_first'])
                elif update.callback_query:
                    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['create_account_first'])
                return
        account = context.user_data.get('account')
        if not selected_lang and account:
            selected_lang = account.language  # Replace with the actual field name for language in your Account model

        # Fetch products related to the account using sync_to_async for Django ORM query
        products = await sync_to_async(list)(MenuItem.objects.filter(account=account))

        if not products:
            await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_products_available'])
            return

        # Create InlineKeyboard with product names as options
        keyboard = []
        for product in products:
            keyboard.append([InlineKeyboardButton(product.item, callback_data=f"delete_product_{product.id}")])

        keyboard.append([InlineKeyboardButton(MESSAGES[selected_lang]['cancel'], callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.message.reply_text(
            MESSAGES[selected_lang]['select_product_to_delete'],
            reply_markup=reply_markup
        )

    except Exception as e:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['error_occurred'].format(error=str(e)))


async def delete_selected_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the user's selected language
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
    account = context.user_data.get('account')
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model

    query = update.callback_query.data
    product_id = query.split("_")[-1]  # Extract the product ID from the callback data

    try:
        # Fetch and delete the selected product
        product = await sync_to_async(MenuItem.objects.get)(id=product_id)
        await sync_to_async(product.delete)()

        await update.callback_query.message.reply_text(
            MESSAGES[selected_lang]['product_deleted'].format(product_name=product.item)
        )
        await show_start_message(update, context, account)

    except MenuItem.DoesNotExist:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['product_not_exist'])
        await show_start_message(update, context, account)
    except Exception as e:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['error_occurred'].format(error=str(e)))


async def handle_image_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the user's selected language
    print("wewewewe")
    selected_lang = context.user_data.get('lang', 'en')  # Default to 'en' if language is not set

    if not update.message.photo:
        if update.message.video:
            await update.message.reply_text(MESSAGES[selected_lang]['video_upload'])
            return
        elif update.message.document:
            await update.message.reply_text(MESSAGES[selected_lang]['document_upload'])
            return
        else:
            await update.message.reply_text(MESSAGES[selected_lang]['no_image_upload'])
            return

    # Check the state and handle accordingly
    print(context.user_data.get('state'))
    if context.user_data.get('state') == 'awaiting_logo':
        await handle_logo(update, context)
    elif context.user_data.get('state') in ['awaiting_product_image', 'awaiting_image']:
        print("inside handle_product_image")
        await handle_product_image(update, context)
    elif context.user_data.get("state") == "awaiting_new_category_picture":
        await handle_uploaded_picture(update, context)
    elif context.user_data.get('state') == 'awaiting_add_new_image':
        # Get the menuitem_id from user_data
        product_id = context.user_data.get('menuitem_id')
        menu_item = await sync_to_async(MenuItem.objects.get)(id=product_id)
        chat_id = update.message.chat.id
        
        # Set default language to English ('en') initially
       

        # Assuming context.user_data['account'] has the logged-in account details
        account = context.user_data.get('account')
        
        if not account:
            try:
                account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
                context.user_data['account'] = account  # Cache the account in user_data
            except Account.DoesNotExist:
                keyboard = [
                    [InlineKeyboardButton(MESSAGES['en']['buttons']['add_account'], callback_data="add_account")],
                    [InlineKeyboardButton(MESSAGES['en']['buttons']['cancel'], callback_data="cancel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.callback_query.message.reply_text(
                    MESSAGES['en']['no_account'],
                    reply_markup=reply_markup
                )
                return

        # Set the user's language if available in the account, otherwise use 'en' (English)
        if account and account.language:
            selected_lang = account.language

        # Check if the user sent an image
        await update.message.reply_text(MESSAGES[selected_lang]['downloading_image'])

        try:
            # Download the product image
            product_image_file = await update.message.photo[-1].get_file()
            product_image_path = f"static/img/items/{context.user_data.get('chat_id', update.message.chat.id)}_product_{int(time.time())}.jpg"
            await product_image_file.download_to_drive(product_image_path)

            # Save the photo in the MenuItemPhoto model
            menuitem_id = context.user_data.get('menuitem_id')  # Get the menu item ID from user data

            # Ensure that the MenuItem ID exists in the context
            if menuitem_id:
                # Create a new MenuItemPhoto instance
                menu_item_photo = MenuItemPhoto(
                    account=account,
                    menuitem_id=menuitem_id,
                    picture=product_image_path  # Save the image path here
                )
                await sync_to_async(menu_item_photo.save)()  # Save to the database asynchronously

                await update.message.reply_text(MESSAGES[selected_lang]['image_downloaded_successfully'])

                # Ask if they want to upload another photo
                
                await update.message.reply_text(MESSAGES[selected_lang]['image_added_success'])

            else:
                await update.message.reply_text(MESSAGES[selected_lang]['menuitem_id_missing'])

        except Exception as e:
            await update.message.reply_text(MESSAGES[selected_lang]['image_download_error'].format(error=str(e)))

    elif context.user_data.get('state') == 'awaiting_new_image':
        print("inside awaiting_new_image")
        await update_product_image(update, context)

    elif context.user_data.get("state") == "awaiting_cover_upload":
        await handle_cover_upload(update, context)

    elif context.user_data.get('state') == 'awaiting_another_new_image':
        await upload_another_photo(update, context)

    elif context.user_data.get("state") == "awaiting_another_cover_image":
        await upload_another_cover_yes(update, context)

    elif context.user_data.get('state') == 'awaiting_edit_logo':
        await handle_edit_logo(update, context)
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['read_message_again'])



async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.callback_query.message.chat.id
    
    # Set default language to English ('en') initially
    selected_lang = 'en'

    # Assuming context.user_data['account'] has the logged-in account details
    account = context.user_data.get('account')
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account  # Cache the account in user_data
        except Account.DoesNotExist:
            keyboard = [
                [InlineKeyboardButton(MESSAGES['en']['buttons']['add_account'], callback_data="add_account")],
                [InlineKeyboardButton(MESSAGES['en']['buttons']['cancel'], callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.message.reply_text(
                MESSAGES['en']['no_account'],
                reply_markup=reply_markup
            )
            return

    # Set the user's language if available in the account, otherwise use 'en' (English)
    if account and account.language:
        selected_lang = account.language

    # Fetch the products for the account using sync_to_async to avoid synchronous operation errors
    products = await sync_to_async(list)(MenuItem.objects.filter(account=account))

    if not products:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_products'])
        return

    # Create inline buttons for each product
    keyboard = []
    for product in products:
        keyboard.append([InlineKeyboardButton(product.item, callback_data=f"edit_{product.id}")])

    keyboard.append([InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['cancel'], callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send translated message based on the selected language
    await update.callback_query.message.reply_text(
        MESSAGES[selected_lang]['buttons']['choose_product'],  # Translated message
        reply_markup=reply_markup
    )


async def edit_product_description(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id):
    selected_lang = context.user_data.get('lang')
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        # Acknowledge the callback query
        await update.callback_query.answer()
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
        return

    context.user_data['chat_id'] = chat_id 

    account = context.user_data.get('account')

    if not account:
        # Try to retrieve the account again in case it's not in user_data
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account
        except Account.DoesNotExist:
            await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account_found'])
            return
        
    if not selected_lang and account:
        selected_lang = account.language  # Replace with the actual field name for language in your Account model


    # Fetch the product from the database
    try:
        product = await sync_to_async(MenuItem.objects.get)(id=product_id)
        context.user_data['product'] = product  # Cache the product in user_data
        
        # Prompt user to enter new description
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['enter_new_description'])
        context.user_data['state'] = 'awaiting_edit_description'  # Set the state to await description input

    except MenuItem.DoesNotExist:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['product_not_exist'])


async def edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id):
    # Get the user's selected language
    chat_id = update.callback_query.message.chat.id
    
    # Set default language to English ('en') initially
    selected_lang = 'en'

    # Assuming context.user_data['account'] has the logged-in account details
    account = context.user_data.get('account')
    
    if not account:
        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            context.user_data['account'] = account  # Cache the account in user_data
        except Account.DoesNotExist:
            keyboard = [
                [InlineKeyboardButton(MESSAGES['en']['buttons']['add_account'], callback_data="add_account")],
                [InlineKeyboardButton(MESSAGES['en']['buttons']['cancel'], callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.message.reply_text(
                MESSAGES['en']['no_account'],
                reply_markup=reply_markup
            )
            return

    # Set the user's language if available in the account, otherwise use 'en' (English)
    if account and account.language:
        selected_lang = account.language

    # Fetch the selected product by ID
    try:
        product = await sync_to_async(MenuItem.objects.get)(id=product_id)
        context.user_data['product'] = product  # Cache the product in user_data
        print("producttttttttt")
        print(context.user_data['product'])
        # Show buttons for editing options: Name, Price, Image
        keyboard = [
            [InlineKeyboardButton(MESSAGES[selected_lang]['edit_name'], callback_data=f"edit_name_{product.id}")],
            [InlineKeyboardButton(MESSAGES[selected_lang]['edit_price'], callback_data=f"edit_price_{product.id}")],
            [InlineKeyboardButton(MESSAGES[selected_lang]['edit_option'], callback_data=f"edit_options_{product.id}")],
            [InlineKeyboardButton(MESSAGES[selected_lang]['edit_description'], callback_data=f"edit_description_{product.id}")],
            [InlineKeyboardButton(MESSAGES[selected_lang]['edit_image'], callback_data=f"edit_image_{product.id}")],
            [InlineKeyboardButton(MESSAGES[selected_lang]['edit_offer'], callback_data=f"edit_offer_{product.id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.message.reply_text(
            MESSAGES[selected_lang]['selected_product'].format(product.item),
            reply_markup=reply_markup
        )

    except MenuItem.DoesNotExist:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['product_not_exist'])


async def send_website_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the user's selected language
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set

    try:
        account = context.user_data.get('account')
        if not account:
            try:
                if update.message:
                    chat_id = context.user_data.get('chat_id', update.message.chat.id)
                elif update.callback_query:
                    chat_id = context.user_data.get('chat_id', update.callback_query.message.chat.id)

                account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
                context.user_data['account'] = account  # Cache the account in user_data
            except Account.DoesNotExist:
                keyboard = [
                    [InlineKeyboardButton(MESSAGES[selected_lang]['add_account'], callback_data="add_account")],
                    [InlineKeyboardButton(MESSAGES[selected_lang]['cancel'], callback_data="cancel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.callback_query.message.reply_text(
                    MESSAGES[selected_lang]['no_account_found'],
                    reply_markup=reply_markup
                )
                return
        if account and account.language:
            selected_lang = account.language

        # Generate the website URL
        username = account.username
        website_url = f"tidy-taps.com/f/{quote(username)}"

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
        await update.callback_query.message.reply_text(
            MESSAGES[selected_lang]['website_url'].format(website_url=website_url)
        )
        await update.callback_query.message.reply_photo(photo=qr_bytes, caption=MESSAGES[selected_lang]['qr_code_caption'])
    
    except Exception as e:
        await update.callback_query.message.reply_text(f"An error occurred: {str(e)}")


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the user's selected language
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
    account = context.user_data.get('account')
    if account and account.language:
        selected_lang = account.language
    # Handle video upload scenario
    if context.user_data.get('state') == "awaiting_logo":
        await update.message.reply_text(MESSAGES[selected_lang]['video_for_logo'])
    
    elif context.user_data.get('state') == "awaiting_product_image":
        await update.message.reply_text(MESSAGES[selected_lang]['video_for_product_image'])
    
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['general_video_upload'])


async def handle_product_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
    product = context.user_data.get('product')
    account = context.user_data.get('account')
    if account and account.language:
        selected_lang = account.language
    if product:
        # Example: handle updating the product name (similarly handle other fields)
        product.item = update.message.text
        await sync_to_async(product.save)()

        await update.message.reply_text(MESSAGES[selected_lang]['product_update_success'].format(product.item))
        context.user_data.pop('product')  # Clear product from context after update
    else:
        await update.message.reply_text(MESSAGES[selected_lang]['product_not_found'])

async def start_editing_name(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id):
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
    account = context.user_data.get('account')
    if account and account.language:
        selected_lang = account.language

    try:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['edit_product_name'])
        context.user_data['state'] = 'awaiting_new_name'
    except Exception as e:
        print(e)
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['product_not_found'])


async def start_editing_price(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id):
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
    account = context.user_data.get('account')
    if account and account.language:
        selected_lang = account.language
    product = context.user_data.get('product')

    try:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['edit_product_price'])
        context.user_data['state'] = 'awaiting_new_price'
    except Exception as e:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['product_not_found'])



async def start_editing_contact(update: Update, context: ContextTypes.DEFAULT_TYPE, contact_id):
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
    account = context.user_data.get('account')
    
    # If account language exists, use it
    if account and account.language:
        selected_lang = account.language

    try:
        # Retrieve the contact based on the provided contact_id
        contact = await sync_to_async(Contacts.objects.get)(id=contact_id, account=account)
        context.user_data['contact'] = contact  # Store the contact in user_data for future reference

        # Prompt the user to edit the phone number
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['edit_contact_phone'])
        
        # Set the state to indicate that the bot is waiting for a new phone number
        context.user_data['state'] = 'awaiting_new_contact'
    except Contacts.DoesNotExist:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['contact_not_found'])


#async def edit_image_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
#    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
#    account = context.user_data.get('account')
    
    # If account language exists, use it
#    if account and account.language:
#        selected_lang = account.language
#    product_id = int(query.data.split("_")[2])  # Extract the product ID

    # Show options to Add or Remove the image
#    keyboard = [
#        [InlineKeyboardButton(MESSAGES[selected_lang]['add_image'], callback_data=f"add_image_{product_id}")],
#        [InlineKeyboardButton(MESSAGES[selected_lang]['remove_image'], callback_data=f"remove_image_{product_id}")]
#    ]
#    reply_markup = InlineKeyboardMarkup(keyboard)

#    await update.callback_query.message.reply_text(
#        MESSAGES[selected_lang]['choose_image_action'],
#        reply_markup=reply_markup
#    )

async def start_editing_image(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id):
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
    account = context.user_data.get('account')
    if account and account.language:
        selected_lang = account.language
    try:
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['upload_product_image'])
        context.user_data['state'] = 'awaiting_new_image'
        context.user_data['product_id'] = product_id
    except Exception as e:
        print(e)
        await update.callback_query.message.reply_text(MESSAGES[selected_lang]['error_message'].format(str(e)))



async def edit_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()  # Acknowledge the callback
    context.user_data['state'] = 'awaiting_title_update'
    
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
    account = context.user_data.get('account')
    if account and account.language:
        selected_lang = account.language
    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['enter_new_title'])

async def cancel_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()  # Clear the current state and any cached data
    
    selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
    account = context.user_data.get('account')
    if account and account.language:
        selected_lang = account.language
    await update.message.reply_text(MESSAGES[selected_lang]['process_canceled'])



async def awaiting_delivery_fee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        selected_lang = context.user_data.get('lang')  # Default to 'en' if language is not set
        account = context.user_data.get('account')
        if account and account.language:
            selected_lang = account.language
        delivery_fee = float(update.message.text)
        context.user_data['delivery_fee'] = delivery_fee

        # Confirm the fee
        await update.message.reply_text(MESSAGES[selected_lang]['delivery_fee_set'].format(delivery_fee))

        # Clear the state
        context.user_data.pop('state', None)
    
    except ValueError:
        await update.message.reply_text(MESSAGES[selected_lang]['invalid_delivery_fee'])

# Handle button clicks
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()


    selected_lang = 'en'  # Default to 'en'

    # Try to get the user's account and their language preference
    chat_id = query.message.chat.id
    try:
        account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
        selected_lang = account.language if account.language else 'en'  # Use the user's preferred language
    except Account.DoesNotExist:
        # If the account does not exist, continue with the default language ('en')
        pass


    if query.data == "add_account":
        await add_account(update, context)

    elif query.data.startswith("lang_"):
        selected_lang = query.data.split('_')[1]  # Get the language code (e.g., 'en', 'ar')
        chat_id = query.message.chat.id

        if query.data == 'lang_en':
            context.user_data['lang'] = 'en'
        elif query.data == 'lang_ar':
            context.user_data['lang'] = 'ar'
        # Fetch or create the user's account and save the language
        

        try:
            account = await sync_to_async(Account.objects.get)(telegramId=chat_id)
            account.language = selected_lang
            await sync_to_async(account.save)()
            context.user_data['account'] = account

        except Exception as e: 
            keyboard = [
                [InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['add_account'], callback_data="add_account")],
                [InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['cancel'], callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if update.callback_query:
                await update.callback_query.message.reply_text(
                    MESSAGES[selected_lang]['no_account'],
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    MESSAGES[selected_lang]['no_account'],
                    reply_markup=reply_markup
                )
            return
        
        print("account.language")
        print(account.language)
        print("context.user_data['lang']")
        print(context.user_data['lang'])
        # Show the welcome message in the selected language
        await show_start_message(update, context, account)

    elif query.data == "add_product":
        
        await add_product(update, context)
    
    elif query.data == "settings":
        
        owned_accounts = await sync_to_async(list)(Account.objects.filter(owner=account.telegramId))

        # Prepare buttons for owned accounts
        account_buttons = [
            InlineKeyboardButton(account.username, callback_data=f"switch_account_{account.id}")
            for account in owned_accounts
        ]

        # Add the "Add Another Account" button
        reply_keyboard = [
            [InlineKeyboardButton(MESSAGES[selected_lang]['add_another_account'], callback_data="add_another_account")]
        ]

        # Add the account buttons
        if account_buttons:
            reply_keyboard.extend([[btn] for btn in account_buttons])

        # Create the InlineKeyboardMarkup
        reply_markup = InlineKeyboardMarkup(reply_keyboard)

        # Send the reply message with the button
        await update.callback_query.message.reply_text(
            MESSAGES[selected_lang]['settings_prompt'],
            reply_markup=reply_markup
        )

    elif query.data.startswith("switch_account_"):
        target_account_id = int(query.data.split("_")[2])

        # Update the current account and target account
        current_account = await sync_to_async(Account.objects.get)(telegramId=account.telegramId)
        target_account = await sync_to_async(Account.objects.get)(id=target_account_id)

        # Clear the telegramId of the current account
        current_account.telegramId = ""
        await sync_to_async(current_account.save)()

        # Assign the telegramId to the target account
        target_account.telegramId = account.telegramId
        await sync_to_async(target_account.save)()

        context.user_data.clear()
        # Confirm the switch to the user
        await query.message.reply_text(
            MESSAGES[selected_lang]['switch_account_success'].format(account_name=target_account.username)
        )

        await show_start_message(update, context,target_account )

    elif query.data == "add_another_account":
        if account.subscription_plan == "free":
            # Send upgrade plan message for free users
            await query.message.reply_text(MESSAGES[account.language]["upgrade_plan_message"])
        else:
            context.user_data['lang'] = selected_lang
            context.user_data['add_another_account'] = account.telegramId
            await add_account(update, context)
        
    elif query.data.startswith("delete_city_"):
        city_to_delete = update.callback_query.data[len('delete_city_'):]

        # Delete the delivery for the selected city asynchronously
        try:
            # Get the delivery for the selected city and account
            delivery = await sync_to_async(Delivery.objects.get)(account=account, id=city_to_delete)

            # Delete the delivery asynchronously
            await sync_to_async(delivery.delete)()

            await update.callback_query.message.reply_text(
                MESSAGES[selected_lang]['delivery_deleted'] % delivery.city
            )
        except Delivery.DoesNotExist:
            await update.callback_query.message.reply_text(MESSAGES[selected_lang]['delivery_not_found'])
        # Reset the state
        context.user_data['state'] = None
        await show_start_message(update, context, account)

    elif query.data == "upgrade_plan":
        await query.message.reply_text(MESSAGES[selected_lang]["upgrade_plan_message"])

    elif query.data == "edit_style":
        await query.message.reply_text(MESSAGES[selected_lang]["choose_theme"])

        # Theme 1
        theme_1_photo_path = "static/img/theme1.jpeg"  # Replace with the actual file path
        theme_1_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                MESSAGES[selected_lang]["preview"], 
                web_app=WebAppInfo(url=f"https://www.tidy-taps.com/f/District")
            ),
                InlineKeyboardButton(MESSAGES[selected_lang]["select"], callback_data="select_theme1")
            ]
        ])
        with open(theme_1_photo_path, "rb") as photo:
            await query.message.reply_photo(
                photo=InputFile(photo),
                caption="✨ Theme 1 (Light): A clean and bright look!",
                reply_markup=theme_1_keyboard
            )

        # Theme 2
        theme_2_photo_path = "static/img/theme2.jpeg"  # Replace with the actual file path
        theme_2_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                MESSAGES[selected_lang]["preview"], 
                web_app=WebAppInfo(url=f"https://www.tidy-taps.com/p/District")
            ),
                InlineKeyboardButton(MESSAGES[selected_lang]["select"], callback_data="select_theme2")
            ]
        ])
        with open(theme_2_photo_path, "rb") as photo:
            await query.message.reply_photo(
                photo=InputFile(photo),
                caption="🌙 Theme 2 (Dark): A sleek and modern design!",
                reply_markup=theme_2_keyboard
            )
    
    
    elif query.data == "select_theme1":
        if account.subscription_plan == "free":
            # Send upgrade plan message for free users
            await query.message.reply_text(MESSAGES[account.language]["upgrade_plan_message"])
        else:
            # Update the selected theme safely
            account.selected_theme = "f"  # Theme 1 identifier
            await sync_to_async(account.save)()  # Use sync_to_async to save
            await query.message.reply_text(
                MESSAGES[account.language]["theme_selected_message"].format(theme="Theme 1")
            )

    elif query.data == "select_theme2":
        if account.subscription_plan == "free":
            # Send upgrade plan message for free users
            await query.message.reply_text(MESSAGES[account.language]["upgrade_plan_message"])
        else:
            # Update the selected theme safely
            account.selected_theme = "p"  # Theme 2 identifier
            await sync_to_async(account.save)()  # Use sync_to_async to save
            await query.message.reply_text(
                MESSAGES[account.language]["theme_selected_message"].format(theme="Theme 2")
            )

    elif query.data == "confirm_delete_yes":
        
        await delete_category(update, context)

    elif query.data == "edit_category_menu":
        category_keyboard = [
            [
                InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['add_category'], callback_data="add_category"),
                InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['edit_category'], callback_data="edit_category")
            ],
            [
                InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['delete_category'], callback_data="delete_category")
            ]
        ]
        category_reply_markup = InlineKeyboardMarkup(category_keyboard)
        
        # Send submenu options to the user
        await update.callback_query.message.reply_text(
            MESSAGES[selected_lang]['choose_category_action'],
            reply_markup=category_reply_markup
        )

    elif query.data == "edit_coupons":
        coupon_keyboard = [
            [
                InlineKeyboardButton(MESSAGES[selected_lang]['Add_Coupon'], callback_data="add_coupon"),
                InlineKeyboardButton(MESSAGES[selected_lang]['Remove_Coupon'], callback_data="remove_coupon"),
            ],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(coupon_keyboard)
        await update.callback_query.message.reply_text(
            MESSAGES[selected_lang]['ask_for_edit_coupons'],
            reply_markup=reply_markup
        )

    elif query.data == "add_coupon":
        if account.subscription_plan == "free":
            await query.message.reply_text(MESSAGES[selected_lang]["upgrade_plan_message"])
        else:
            await handle_add_coupon(update, context)
    elif query.data == "remove_coupon":
        if account.subscription_plan == "free":
            await query.message.reply_text(MESSAGES[selected_lang]["upgrade_plan_message"])
        else:
            await handle_remove_coupon(update, context)
            
    elif query.data == "edit_category":
        await handle_edit_category_menu(update, context, selected_lang)

    elif query.data.startswith("confirm_delete_category_"):
        await confirm_delete_category(update, context) 

    elif query.data.startswith("edit_category_name_"):
        await handle_category_selection(update, context)
    elif query.data.startswith("edit_catgetory_picture_"):
        await handle_category_picture_edit(update, context)
    elif query.data.startswith("edit_category_"):
        category_id = int(query.data.split("_")[-1])
        category_keyboard = [
            [
                InlineKeyboardButton(MESSAGES[selected_lang]['edit_name'], callback_data=f"edit_category_name_{category_id}"),
                InlineKeyboardButton(MESSAGES[selected_lang]['edit_image'], callback_data=f"edit_catgetory_picture_{category_id}")
            ],
           
        ]
        category_reply_markup = InlineKeyboardMarkup(category_keyboard)
        
        # Send submenu options to the user
        await update.callback_query.message.reply_text(
            MESSAGES[selected_lang]['what_to_edit'],
            reply_markup=category_reply_markup
        )
        #await handle_category_selection(update, context)
    
    elif query.data == "edit_addresses":
        await show_address_list(update, context)
    
    elif query.data.startswith("edit_address_"):
        await edit_address(update, context)  # Call the edit_address function

    elif query.data == "edit_social_media":
        await show_social_media_options(update, context)

    elif query.data.startswith("change_currency"):
        # Navigate to another page
        await show_currency_page(update, context)

    elif query.data.startswith("currency_page_"):
        page = int(query.data.split("_")[-1])
        await show_currency_page(update, context, page)

    elif query.data.startswith("currency_"):
        await set_currency(update, context)

    elif query.data == "edit_facebook":
        await query.message.reply_text(MESSAGES[selected_lang]['enter_facebook_link'])
        context.user_data['social_media'] = 'facebook'
        context.user_data['state'] = 'awaiting_facebook_link'

    elif query.data == "edit_instagram":
        await query.message.reply_text(MESSAGES[selected_lang]['enter_instagram_link'])
        context.user_data['social_media'] = 'instagram'
        context.user_data['state'] = 'awaiting_instagram_link'

    elif query.data == "edit_whatsapp":
        await query.message.reply_text(MESSAGES[selected_lang]['enter_whatsapp_link'])
        context.user_data['social_media'] = 'whatsapp'
        context.user_data['state'] = 'awaiting_whatsapp_link'

    elif query.data == "edit_delivery_fees":
        await handle_edit_delivery_fees(update, context)
    elif query.data == "add_delivery":
        await handle_add_delivery(update, context)
    elif query.data == "edit_existing_delivery":
        await handle_edit_delivery(update, context)
    elif query.data == "delete_delivery":
        await handle_delete_delivery(update, context)
    elif query.data == "go_back_to_main_menu":
        await show_start_message(update, context, account)  # Assuming this function shows the main menu options

    elif query.data == "get_analytics":
        account_id = account.id  # Assuming you have an account object with an id field
        print("account_id")
        print(account_id)

        loading_message_text = MESSAGES[selected_lang]['loading_message']
        loading_message = await query.message.reply_text(loading_message_text, disable_notification=True)
        # Constructing the API call
        api_url = "https://us.posthog.com/api/projects/97740/query/"
        headers = {
            'Authorization': 'Bearer phx_q3dOBgCDf270CsMd3TxVAYGsm8Gaxn0vwQb7WJ5bRURs8oK',
            'Content-Type': 'application/json'
        }
        
        query_data = {
            "query": {
                "kind": "HogQLQuery",
                "query": f"SELECT COUNT(*) AS total_views, COUNT(DISTINCT distinct_id) AS total_visits, "
                        f"AVG(toFloat(properties.$session_duration)) AS avg_visit_duration "
                        f"FROM events WHERE event = 'account_page_view' AND properties.account_id = '{account_id}'"
            }
        }

        # Make the request to PostHog API
        response = requests.post(api_url, headers=headers, data=json.dumps(query_data))
        
        

        # Check if the response was successful
        if response.status_code == 200:
            result = response.json()['results'][0]
            total_views = result[0]
            total_visits = result[1]

            analytics_message = MESSAGES[selected_lang]['get_analytics']
            # Reply back with the analytics information
            await loading_message.edit_text(analytics_message.format(
                account_id=account_id, 
                total_views=total_views, 
                total_visits=total_visits
            ),
            parse_mode="Markdown"
            )
        else:
            failed_message = MESSAGES[selected_lang]['failed_fetch']
            await query.message.reply_text(failed_message.format(status_code=response.status_code))

    elif query.data == "edit_tiktok":
        await query.message.reply_text(MESSAGES[selected_lang]['enter_tiktok_link'])
        context.user_data['social_media'] = 'tiktok'
        context.user_data['state'] = 'awaiting_tiktok_link'

    elif query.data == "edit_cover":
        account = context.user_data.get('account')

        # Get the user's selected language, defaulting to 'en' if not set
        selected_lang = context.user_data.get('lang')
        print("selected_lang")
        print(selected_lang)
        if update.message:
            chat_id = update.message.chat.id
        elif update.callback_query:
            chat_id = update.callback_query.message.chat.id
            # Acknowledge the callback query
            await update.callback_query.answer()
        else:
            await update.message.reply_text(MESSAGES[selected_lang]['unable_to_determine_chat_id'])
            return

        context.user_data['chat_id'] = chat_id 

        if not account:
            try:
                account = await sync_to_async(Account.objects.get)(telegramId=chat_id)  # Wrap ORM call with sync_to_async
                context.user_data['account'] = account  # Cache the account for future use
            except Account.DoesNotExist:
                if update.message:
                    await update.message.reply_text(MESSAGES[selected_lang]['no_account'])
                elif update.callback_query:
                    await update.callback_query.message.reply_text(MESSAGES[selected_lang]['no_account'])
                return
        
        if not selected_lang and account:
            selected_lang = account.language  # Replace with the actual field name for language in your Account model

        
        context.user_data['state'] = 'cover_action'
        await query.answer()
        
        # Provide options for Add or Delete cover
        keyboard = [
            [
                InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['add_cover'], callback_data="add_cover"),
                InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['delete_cover'], callback_data="delete_cover")
            ],
            [
                InlineKeyboardButton(MESSAGES[selected_lang]['cancel'], callback_data="cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(MESSAGES[selected_lang]['choose_cover_action'], reply_markup=reply_markup)
        #context.user_data['state'] = 'awaiting_cover_upload'  # Set state to indicate cover upload is expected
        #await query.answer()
        #await query.message.reply_text(MESSAGES[selected_lang]['upload_cover_instruction'])  # Prompt user for cover upload
    # Other button handlers...
    elif query.data == "delete_cover":
        await handle_delete_cover_action(update, context)

    elif query.data.startswith("delete_cover_"):
        cover_id = int(query.data.split("_")[-1])
        await delete_cover(cover_id, update, context)


    elif query.data == "add_cover":
        context.user_data['state'] = 'awaiting_cover_upload'
        await query.answer()
        await query.message.reply_text(MESSAGES[selected_lang]['upload_cover_instruction'])
    elif query.data == "edit_whatsapp_number":
        await query.message.reply_text(MESSAGES[selected_lang]['enter_new_phone_number'])
        context.user_data['state'] = "awaiting_phone_number"  # Set a flag to expect the phone number next
        
    elif query.data == "add_options_yes":
        await handle_add_options_yes(update, context)

    elif query.data == "add_another_option_yes":
        # Ask for the new option title
        option_title_prompt = MESSAGES[selected_lang]['provide_option_title']
        await query.message.reply_text(option_title_prompt)

        # Set state to collect the new option title
        context.user_data['collecting_option_title'] = True
        context.user_data['state'] = 'awaiting_option_title'

    elif query.data == "add_another_option_no":

        await query.message.reply_text(MESSAGES[selected_lang]['options_completed'])
        
        await show_start_message(update, context, account)

        # Finalize the product or move to the next stage
    elif query.data == "add_options_no":
        context.user_data.pop('state', None)
        await show_start_message(update, context, account)

    elif query.data == "add_more_option_yes":
        # Ask the user for the next option value
        option_values_prompt = MESSAGES[selected_lang]['provide_single_option_value']
        await query.message.reply_text(option_values_prompt)

        # Set state to collect the next option value
        context.user_data['collecting_value'] = True
        context.user_data['state'] = 'awaiting_single_option_value'

    elif query.data == "add_more_option_no":
        #await query.message.reply_text(MESSAGES[selected_lang]['no_more_options'])
        await store_option_in_db(context)
        another_option_prompt = MESSAGES[selected_lang]['add_another_option_title']

        another_option_keyboard = [
            [
                InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['yes'], callback_data="add_another_option_yes"),
                InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['no'], callback_data="add_another_option_no")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(another_option_keyboard)

        await query.message.reply_text(another_option_prompt, reply_markup=reply_markup)


    elif query.data.startswith("edit_description_"):
        product_id = query.data.split("_")[2]  # Extract product ID from the callback data

        await edit_product_description(update, context, product_id)

    elif query.data.startswith('remove_coupon_'):
        await handle_coupon_removal(update, context)
    elif query.data == 'edit_product':
        await query.message.reply_text(MESSAGES[selected_lang]['buttons']['edit_product'])
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
        print("edit imageeeeeeeee")
        product_id = int(query.data.split("_")[2])  # Extract the product ID
        #await start_editing_image(update, context, product_id)
        keyboard = [
            [InlineKeyboardButton(MESSAGES[selected_lang]['add_image'], callback_data=f"add_image_{product_id}")],
            [InlineKeyboardButton(MESSAGES[selected_lang]['remove_image'], callback_data=f"remove_image_{product_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.message.reply_text(
            MESSAGES[selected_lang]['choose_image_action'],
            reply_markup=reply_markup
        )

    elif query.data.startswith('edit_offer_'):
        query = update.callback_query
        chat_id = query.message.chat.id

        # Extract product ID from the callback data
        product_id = int(query.data.split('_')[-1])
        
        try:
            product = await sync_to_async(MenuItem.objects.get)(id=product_id)
            context.user_data['product'] = product

            # Prompt the user to enter the new offer details, including the product price
            message = MESSAGES[context.user_data.get('account').language]['enter_offer'].format(
                product_name=product.item,
                product_price=product.price
            )
            
            await query.message.reply_text(message)
            context.user_data['state'] = 'WAITING_FOR_OFFER'
            return 'WAITING_FOR_OFFER'  # Set the state to wait for the user's input

        except MenuItem.DoesNotExist:
            await query.message.reply_text(
                MESSAGES[context.user_data.get('account').language]['product_not_exist']
            )

    elif query.data.startswith("add_image_"):
        product_id = int(query.data.split("_")[2])  # Extract the product ID
        context.user_data['menuitem_id'] = product_id  # Store product ID in user_data
        
        context.user_data['state'] = 'awaiting_add_new_image'
        await query.message.reply_text(MESSAGES[selected_lang]['awaiting_image'])

    elif query.data.startswith("remove_image_"):
        product_id = int(query.data.split("_")[2])  # Extract the product ID

        # Get the MenuItem and its associated images
        menu_item = await sync_to_async(MenuItem.objects.get)(id=product_id)
        main_image = menu_item.picture
        additional_images = await sync_to_async(list)(menu_item.menuitem_photos.all())
        
        images_sent = False  # Track if any images were sent

        # If the main image exists, send it with a remove button
        print("main_image")
        print(main_image)
        
        if main_image:
            main_image_path = main_image.path
            with open(main_image_path, 'rb') as image_file:
                keyboard = [
                    [InlineKeyboardButton(
                        text=MESSAGES[selected_lang]['remove_image'],
                        callback_data=f"confirm_remove_image_{menu_item.id}_"  # Use empty string after product ID for main image
                    )]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.callback_query.message.reply_photo(
                    photo=InputFile(image_file),
                    reply_markup=reply_markup
                )
            images_sent = True

        # Send each additional image with a remove button
        for image in additional_images:
            image_path = image.picture.path
            with open(image_path, 'rb') as image_file:
                keyboard = [
                    [InlineKeyboardButton(
                        text=MESSAGES[selected_lang]['remove_image'],
                        callback_data=f"confirm_remove_image_{product_id}_{image.id}"
                    )]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.callback_query.message.reply_photo(
                    photo=InputFile(image_file),
                    reply_markup=reply_markup
                )
            images_sent = True

        # If there are no images to show
        if not images_sent:
            await update.callback_query.message.reply_text(
                text=MESSAGES[selected_lang]['no_images_to_remove']
            )

    elif query.data.startswith("confirm_remove_image_"):
        image_id_str = query.data.split("_")[4]  # Extract the image ID or empty string
        
        print("image_id_str")
        print(image_id_str)
        print(query.data.split("_"))
        if image_id_str == "":
            # Handle main image removal
            product_id = int(query.data.split("_")[3])  # Get the product ID from callback data
            menu_item = await sync_to_async(MenuItem.objects.get)(id=product_id)
            
            # Delete the main image file
            await sync_to_async(menu_item.picture.delete)(save=True)
            
            # Notify the user about successful main image removal
            await update.callback_query.message.reply_text(
                text=MESSAGES[selected_lang]['image_removed_success']
            )
        else:
            image_id_str = query.data.split("_")[4]
            # Handle additional image removal
            image_id = int(image_id_str)  # Convert the ID from string to int
            image = await sync_to_async(MenuItemPhoto.objects.get)(id=image_id)
            
            # Delete the image
            await sync_to_async(image.delete)()
            
            # Notify the user about successful additional image removal
            await update.callback_query.message.reply_text(
                text=MESSAGES[selected_lang]['image_removed_success']
            )



    elif query.data.startswith("edit_store_info"):
        await edit_store_info(update, context)

    elif query.data == "delete_category":
        await show_categories_for_deletion(update, context)  # Call the function to show categories for deletion

    elif query.data == "delete_address_list":
        await show_address_list_for_deletion(update, context)  # Show addresses for deletion

    elif query.data == "delete_contact_list":
        await show_delete_contact_list(update, context)  # Call the function to show categories for deletion

    elif query.data == "upload_another_photo":
        context.user_data['state'] = 'awaiting_another_new_image'
        await query.message.reply_text(MESSAGES[selected_lang]['awaiting_image'])

    elif query.data == "upload_another_cover_yes":
        context.user_data['state'] = "awaiting_another_cover_image"
        await query.message.reply_text(MESSAGES[selected_lang]['upload_another_cover_inst'])


        
    
    elif query.data == "no_more_covers":
        await no_more_covers(update, context)

    elif query.data == "no_more_photos":
        await no_more_photos(update, context)
        
    elif query.data == "get_website_qr":  # New handler for the QR code
        await send_website_qr(update, context)

    elif query.data == "edit_delivery_fees":  
        await handle_edit_delivery_fees(update, context)
        await query.message.reply_text(MESSAGES[selected_lang]['enter_delivery_fee'])
        context.user_data['state'] = 'awaiting_delivery_fee'

    elif query.data.startswith("delete_address_"):
        await delete_address(update, context)  # Handle the address deletion

    elif query.data == "edit_contacts":
        await handle_edit_contacts(update, context)
        
    elif query.data.startswith("edit_contact_"):
        contact_id = query.data.split("_")[-1]  # Extract contact ID from callback data
        await start_editing_contact(update, context, contact_id)
        

    elif query.data.startswith("delete_category_"):
        await delete_category(update, context)

    elif query.data.startswith("confirm_delete_contact_"):
        contact_id = query.data.split("_")[3]
        await confirm_delete_contact(update, context, contact_id)

    elif query.data == "delete_contact_confirm":
        await delete_selected_contact(update, context)

    elif query.data.startswith("edit_logo"):
        await edit_logo(update, context)

    elif query.data.startswith("create_new_category") or query.data == "add_category":
        await query.message.reply_text(MESSAGES[selected_lang]['enter_new_category'])
        context.user_data['state'] = 'awaiting_category'

    elif query.data.startswith("create_new_contact"):
        await query.message.reply_text(MESSAGES[selected_lang]['enter_new_contacts'])
        context.user_data['state'] = 'awaiting_contact'

    

    elif query.data.startswith("create_new_address"):
        await query.message.reply_text(MESSAGES[selected_lang]['enter_new_addresses'])
        context.user_data['state'] = 'awaiting_address_details'


    elif query.data.startswith("category_"):  # Handle category selection
        category_name = query.data.split("_")[1]  # Extract category name from callback data
        context.user_data['category_name'] = category_name  # Store the selected category name
        await handle_category(update, context)  # Call handle_category to process the selected category


    elif query.data.startswith("edit_title"):
        await edit_title(update, context)

    elif query.data == "edit_color":
        await handle_edit_color(update, context)
    elif query.data == "edit_primary_color":
        await edit_primary_color(update, context)

    elif query.data == "edit_secondary_color":
        await edit_secondary_color(update, context)

    elif query.data == "Edits_contacts":
        await handle_edit_contacts(update, context)

    elif query.data.startswith("add_new_choice_"):
        option_id = query.data.split("_")[-1]
        await add_new_choice(update, context, option_id)

    elif query.data == "add_new_option":
        await handle_add_new_option(update, context)

    elif query.data.startswith("add_another_choice") or query.data == "finish_adding_choices":
        await handle_add_another_choice(update, context)

    elif query.data.startswith("remove_option_"):
        await handle_remove_option(update, context)
    elif query.data.startswith("confirm_remove_option_") or query.data == "cancel_remove_option":
        await handle_confirm_remove_option(update, context)

    elif query.data.startswith("edit_option_choices_"):
        print("we are edit_option_choices_")
        print("wwwwwwwwwwwwwwwwwwwwwwwwwwwwww")
        option_id = query.data.split("_")[3]
        print("option_id")
        print(option_id)
        await edit_option_choices(update, context, option_id)

    elif query.data.startswith("edit_option_title_"):
        print("we are in edit option title")
        await edit_option_title(update, context)

    elif query.data.startswith("edit_option_"):
        print("we are in edit_option")
        print("option_id")

        option_id = query.data.split("_")[-1]
        print("option_id")
        print(option_id)
       
        await handle_edit_option(update, context, option_id)

    elif query.data.startswith("edit_options_"):
        menu_item = query.data.split("edit_options_")[1]
        product = await sync_to_async(MenuItem.objects.get)(id=menu_item)
        context.user_data["menu_item"] = product
        await edit_options(update, context)
    
    elif query.data.startswith("edit_choice_price_"):
        print("we are in edit_choice_price_  ")
        print(query.data.split("_")[3])
        
        await handle_edit_choice_price(update, context)

    elif query.data.startswith("edit_choice_value_"):
        print("we are in edit_choice_value_  ")
        print(query.data.split("_")[3])
        choice_id = query.data.split("_")[3]

        await edit_choice(update, context, choice_id)


    elif query.data.startswith("edit_choice_"):
        choice_id = query.data.split("_")[-1]
        await handle_edit_choice(update, context, choice_id)

        #await edit_choice(update, context, choice_id)
    
    elif query.data == 'delete_product':
        await show_products_for_deletion(update, context)

    elif query.data.startswith('delete_product_'):
        await delete_selected_product(update, context)

    elif query.data.startswith("edit_"):
        product_id = int(query.data.split("_")[1])  # Extract the product ID from the callback data
        await edit_product(update, context, product_id)

    if query.data == "help":
        # Send the help message to the user who requested it
        help_message = MESSAGES[selected_lang]['help']
        await query.message.reply_text(help_message)

        # Send a notification to your Telegram chat (your chat ID)
        user = update.effective_user
        notification_message = f"User {user.username or user.first_name} ({user.id}) has requested help."

        # Get the bot token from the context or directly if available
        bot = context.bot
        await bot.send_message(chat_id="1281643104", text=notification_message)

    elif query.data == "yes":
        account = context.user_data.get('account')
        category_name = context.user_data['category_name']
        new_category = Category(name=category_name, account=account)
        await sync_to_async(new_category.save)()
        context.user_data['category'] = new_category

        # Get the user's selected language
        selected_lang = context.user_data.get('lang') or (account.language if account else 'en')

        # Create an inline keyboard with a "Cancel" button
        keyboard = [
            [InlineKeyboardButton(MESSAGES[selected_lang]['buttons']['cancel'], callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(
            text=MESSAGES[selected_lang]['category_creation_success'].format(category_name=category_name),
            reply_markup=reply_markup
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
    #token = "7888485362:AAGYv9unTDpgW4X3_cVF-RFMqP194UADVwE"   #staging
    token = "6977293897:AAE9OYhwEn75eI6mYyg9dK1_YY3hCB2M2T8"  # Replace with your bot token #production
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
