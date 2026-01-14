import requests
from bs4 import BeautifulSoup
from plyer import  notification
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import telegram
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from webdriver_manager.chrome import ChromeDriverManager
import os
from dotenv import load_dotenv
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading

TOKEN = 
URLS = {}
bot = telegram.Bot(token=TOKEN)
Allowed_users = []
Excluded_words = ["collier", "necklace", "ring", "collana", "ceinture", "cinturón", "boucle", "oreille", "pendetif", "belt", "chaussette", "orecchini",  "melissa", "chaîne"]

async def is_allowed_user(chat_id):
    return chat_id in Allowed_users

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await send_telegram_message(chat_id, f"Your chat ID is: {chat_id}. Please send this to the bot admin to get access.")



# Parse html to try to find differences from the previous reload.
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting for url'):
        await save_url(update, context)
    elif context.user_data.get('waiting for delete'):
        await process_delete(update, context)

async def send_telegram_message(chat_id, message):

   await bot.send_message(chat_id = chat_id, text = message)

async def set_url(update: Update,context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if not await is_allowed_user(chat_id):
        await send_telegram_message(chat_id, "You are not allowed to use this bot")
        return
    await send_telegram_message(chat_id, "hello you are setting up the url for the search, please respond to this message with a valid url ;)")
    context.user_data['waiting for url'] = True

async def save_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if context.user_data.get('waiting for url'):
            url = update.message.text
            if chat_id not in URLS:
                URLS[chat_id] = []
            URLS[chat_id].append(url)
            await send_telegram_message(chat_id, f"Url: {url} is ready for searching...")
            context.user_data['waiting for url'] = False
async def delete_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if not await is_allowed_user(chat_id):
        await send_telegram_message(chat_id, "You are not allowed to use this bot")
        return
    if chat_id not in URLS or not URLS[chat_id]:
        await send_telegram_message(chat_id, "No URLs found to delete.")
        return
    
    await send_telegram_message(chat_id, f"Please reply to this message either with the number or the url that u want to delete")
    context.user_data['waiting for delete']= True

async def process_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id= update.message.chat_id
    if context.user_data.get('waiting for delete'):
        input_value = update.message.text
        try: 

            index = int(input_value) - 1
            if 0<= index < len(URLS[chat_id]):
                removed_url = URLS[chat_id].pop(index)
                await send_telegram_message(chat_id, f"Url {removed_url} has been deleted")
            else:
                await send_telegram_message(chat_id,f"The number is out of range")
        except ValueError:
            url_to_remove = input_value
            if url_to_remove in URLS[chat_id]:
                URLS[chat_id].remove(url_to_remove)
                await send_telegram_message(chat_id, f"The url {url_to_remove} has been deleted")
            else:
                await send_telegram_message(chat_id, f"the url{url_to_remove} was not found in your url list")
        context.user_data['waiting for delete']= False

async def list_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if not await is_allowed_user(chat_id):
        await send_telegram_message(chat_id, "You are not allowed to use this bot")
        return
    if chat_id in URLS and URLS[chat_id]:
        # Crear una lista numerada de URLs
        url_list = "\n".join([f"{i+1}. {url}" for i, url in enumerate(URLS[chat_id])])
        await send_telegram_message(chat_id, f"Here are your current URLs:\n{url_list}")
    else:
        await send_telegram_message(chat_id, "You don't have any URLs saved.")

async def get_driver(): 
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver
    

async def parse_html(chat_id, latest_products):  # latest_products will now be a dict of {url: latest_product}
    driver = None
    try:
        urls = URLS.get(chat_id, [])
        if not urls:
            await send_telegram_message(chat_id, "No URLs found. Please set URLs with /seturl.")
            return latest_products

        driver = await get_driver()

        for url in urls:
            driver.get(url)
            await asyncio.sleep(15)
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            product = soup.find('a', class_="new-item-box__overlay new-item-box__overlay--clickable")
            if not product:
                await send_telegram_message(chat_id, f"No products found at {url}")
                continue

            product_link = product['href']
            product_title = product['title']
            product_info = product_title.split(", ")
            product_name = product_info[0].strip().lower()

            current_product = product_name
            latest_product = latest_products.get(url)
            print(current_product)
            print(latest_product)

            if current_product != latest_product and latest_product != None and not any(word in current_product for word in Excluded_words):
                message = f"There is a new product: {product_info} {product_link}"
                await send_telegram_message(chat_id, message)
                latest_products[url] = current_product
            elif any(word in current_product for word in Excluded_words):
                print("producto excluido por palabra prohibida")
                latest_products[url] = current_product
            else:
                print(f"No new products at {url}")
                latest_products[url] = current_product

        return latest_products

    except Exception as e:
        print(f"Error: {e}")
        await send_telegram_message(chat_id, "An error occurred. Check the URLs or try again later.")
        return latest_products
    finally:
        if driver:
            driver.quit()

latest_product = {}

async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if not await is_allowed_user(chat_id):
        await send_telegram_message(chat_id, "You are not allowed to use this bot")
        return
    await send_telegram_message(chat_id, "search has been initiated...")

    async def monitor():  # A function that allows running parse_html in the background while the bot listens to other commands
        
        while True:
            global latest_product
            latest_product = await parse_html(chat_id, latest_product)
            await asyncio.sleep(40)
    context.user_data['monitor_task'] = asyncio.create_task(monitor())


async def stop_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id =update.message.chat_id
    if not await is_allowed_user(chat_id):
        await send_telegram_message(chat_id, "You are not allowed to use this bot")
        return
    if 'monitor_task' in context.user_data:
        context.user_data['monitor_task'].cancel()
        await send_telegram_message(chat_id, "The search has been stopped you can now change the url or start it again using de commands")
    else:
        await send_telegram_message(chat_id, "There is no active search that can be stopped")

# Comands and handlers



Application = ApplicationBuilder().token(TOKEN).build()

Application.add_handler(CommandHandler("startsearch", start_search))
Application.add_handler(CommandHandler("seturl", set_url))
Application.add_handler(CommandHandler("stopsearch",stop_search))
Application.add_handler(CommandHandler("deleteurl", delete_url))
Application.add_handler(CommandHandler("listurl", list_url))
Application.add_handler(CommandHandler("getchatid", get_chat_id))

Application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))



if __name__ == "__main__":

   Application.run_polling()



