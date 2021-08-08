from pymongo import MongoClient
import foo

from apscheduler.schedulers.blocking import BlockingScheduler
from pymessenger.bot import Bot

ACCESS_TOKEN = foo.ACCESS_TOKEN
VERIFY_TOKEN = foo.VERIFY_TOKEN
bot = Bot(ACCESS_TOKEN)

# Database config
client = MongoClient(foo.MONGO_URI)
db_operations = client.FbMessenger.user

db_collections = {}

db_collections['IamLoved'] = client.FbMessenger.IamLoved
db_collections['IamOk'] = client.FbMessenger.IamOk
db_collections['IamSafe'] = client.FbMessenger.IamSafe
db_collections['LaborAndDelivery'] = client.FbMessenger.LaborAndDelivery
db_collections['LetsDoThis'] = client.FbMessenger.LetsDoThis

scheduler = BlockingScheduler()

@scheduler.scheduled_job("cron", hour=12)
def daily():
    users = list(db_operations.find({}, {"schedule": "None"}))
    print(users)
    for user in users:
        _id = user["_id"]
        try:
            ref = user['ref']
            print(ref)
            if ref in ["IamLoved", "IamOk", "LetsDoThis"]:
                audio_url = f"https://verse-recordings.s3.ap-south-1.amazonaws.com/{_id}/{ref}.mp3"
                bot.send_audio_url(recipient_id=_id, audio_url=audio_url)
        except KeyError:
            continue
        # bot.send_text_message(recipient_id=_id, message="Hello")

scheduler.start()