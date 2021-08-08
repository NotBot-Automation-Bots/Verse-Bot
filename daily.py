from pymongo import MongoClient
import foo

from apscheduler.schedulers.background import BackgroundScheduler
from pymessenger.bot import Bot

ACCESS_TOKEN = foo.ACCESS_TOKEN
VERIFY_TOKEN = foo.VERIFY_TOKEN
bot = Bot(ACCESS_TOKEN)

# Database config
client = MongoClient(foo.MONGO_URI)
db_operations = client.user

db_collections = {}

db_collections['IamLoved'] = client.IamLoved
db_collections['IamOk'] = client.IamOk
db_collections['IamSafe'] = client.IamSafe
db_collections['LaborAndDelivery'] = client.LaborAndDelivery
db_collections['LetsDoThis'] = client.LetsDoThis

scheduler = BackgroundScheduler()

@scheduler.scheduled_job("interval", seconds=10)
def daily():
    users = db_operations.find({"schedule": "Daily"})
    for user in users:
        _id = user["_id"]
        audio_url = f"https://verse-recordings.s3.ap-south-1.amazonaws.com/{user['_id']}/{user['ref']}.mp3"
        # bot.send_audio_url(recipient_id=_id, audio_url=audio_url)
        r = bot.send_text_message(recipient_id=_id, message="Hello")
        print(r.json())

scheduler.start()