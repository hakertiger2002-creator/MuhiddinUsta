from flask import Flask
from threading import Thread
import time
import requests
import os

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def start_keep_alive():
    t = Thread(target=run)
    t.start()

# Render uchun ping funksiyasi
def ping_server():
    while True:
        try:
            # O'z-o'zini ping qilish
            if os.getenv('RENDER', False):
                requests.get('https://your-bot-name.onrender.com')
            time.sleep(300)  # 5 daqiqada bir
        except:
            pass