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

TOKEN = '7471144906:AAEWx_QBRfILSPBzLvqTYFlth2SVHHnAdC0' #os.getenv('Telegram_bot_token')
URLS = {}
bot = telegram.Bot(token=TOKEN)



# Parse html to try to find differences from the previous reload.
async def send_telegram_message(chat_id, message):

   await bot.send_message(chat_id = chat_id, text = message)

async def set_url(update: Update,context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await send_telegram_message(chat_id, "hello you are setting up the url for the search, please respond to this message with a valid url ;)")
    context.user_data['waiting for url'] = True

async def save_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if context.user_data.get('waiting for url'):
            url = update.message.text
            URLS[chat_id] = url 
            await send_telegram_message(chat_id, f"Url: {url} is ready for searching...")
            context.user_data['waiting for url'] = False
        
async def get_driver(): 
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager(version="114.0.5735.90").install()), options=chrome_options)
    return driver
    

async def parse_html(chat_id, latest_product): 
    try: 
        url = URLS.get(chat_id)
        if not url:
            await send_telegram_message(chat_id, "there is no url or its not correct.")
            return latest_product

        driver = await get_driver()
        driver.get(url)
        await asyncio.sleep(15)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        product = soup.find('a', class_="new-item-box__overlay new-item-box__overlay--clickable")
        product_link = product['href']
        product_title = product['title']
        print(product_title)
        product_info = product_title.split(", ")
        product_name = product_info[0].strip().lower()
        
        current_product = product_name
        print(f"actual producto : {current_product}")
        print(f"ultimo producto : {latest_product}")

        if current_product != latest_product and latest_product != "":
            print("there have been changes in the feed, a new upload has been done")
            message = f"hay un nuevo producto :  {product_info} {product_link} "
            await send_telegram_message(chat_id, message)
            return current_product
        else :
            print(f"There is no new products available")
            return current_product
    except Exception as e:
        print(f"Error: {e}")
        await send_telegram_message(chat_id, "An error has ocurred this migth be beacause 2 scenarios:\n 1. The Url u gave was not valid.\n Solution: please type /seturl to set the url again\n 2: the vinted page is down\n Solution: try later :( ")
        return latest_product
    finally:
        if driver:
            driver.quit()

async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    latest_product = ""
    await send_telegram_message(chat_id, "search has been initiated...")

    async def monitor():  # A function that allows running parse_html in the background while the bot listens to other commands
        nonlocal latest_product
        while True:
            latest_product = await parse_html(chat_id, latest_product)
            await asyncio.sleep(40)
    context.user_data['monitor_task'] = asyncio.create_task(monitor())


async def stop_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id =update.message.chat_id
    if 'monitor_task' in context.user_data:
        context.user_data['monitor_task'].cancel()
        await send_telegram_message(chat_id, "The search has been stopped you can now change the url or start it again using de commands")
    else:
        await send_telegram_message(chat_id, "There is no active search that can be stopped")

# Comands

Application = ApplicationBuilder().token(TOKEN).build()

Application.add_handler(CommandHandler("startsearch", start_search))
Application.add_handler(CommandHandler("seturl", set_url))
Application.add_handler(CommandHandler("stopsearch",stop_search))

Application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), save_url))
def start_http_server():

    port = int(os.getenv("PORT", 8080))

    # Iniciar un servidor básico HTTP
    handler = SimpleHTTPRequestHandler
    httpd = HTTPServer(("", port), handler)
    print(f"Serving on port {port}")
    httpd.serve_forever()
if __name__ == "__main__":
   threading.Thread(target=start_http_server).start()
   Application.run_polling()



