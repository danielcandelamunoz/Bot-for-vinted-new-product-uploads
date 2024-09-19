import requests
from bs4 import BeautifulSoup
from plyer import  notification
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import telegram
import asyncio


TOKEN = '7471144906:AAEWx_QBRfILSPBzLvqTYFlth2SVHHnAdC0'
CHAT_ID = '1419980837'
bot = telegram.Bot(token=TOKEN)

# Parse html to try to find differences from the previous reload.
async def send_telegram_message(message):

   await bot.send_message(chat_id = CHAT_ID, text = message)

async def parse_html(url, latest_product):
    try: 
        chrome_options = Options()
        chrome_options.add_argument("--disable-cache")
        service = Service(r'C:\Users\34635\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe')
        driver = webdriver.Chrome(service=service)
        driver.get(url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        product = soup.find('a', class_="new-item-box__overlay new-item-box__overlay--clickable")
        product_title = product['title']
        print(product_title)
        product_info = product_title.split(", ")
        product_name = product_info[0].strip().lower()
        
        current_product = product_name
        print(f"actual producto : {current_product}")
        print(f"ultimo producto : {latest_product}")

        if current_product != latest_product and latest_product != "":
            print("there have been changes in the feed, a new upload has been done")
            message = f"hay un nuevo producto :  {product_info} "
            await send_telegram_message(message)
            return current_product
        else :
            print(f"There is no new products available")
            return current_product
    except Exception as e:
        print(f"Error: {e}")
        return latest_product
    finally:
        if driver:
            driver.quit()

async def main():
    url= "https://www.vinted.es/catalog?search_text=vivienne%20westwood&time=1726310031&price_to=100&currency=EUR&order=newest_first&page=1"
    latest_product = ""

    while True:
        latest_product = await parse_html(url, latest_product)
        await asyncio.sleep(30)
if __name__ == "__main__":
   asyncio.run(main())



