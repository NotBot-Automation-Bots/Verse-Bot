import requests
import foo
import boto3
import mimetypes

from flask import Flask, request
from pymessenger.bot import Bot
from flask_pymongo import PyMongo
from pydub import AudioSegment
from pymongo.errors import DuplicateKeyError

application = Flask(__name__)
ACCESS_TOKEN = foo.ACCESS_TOKEN
VERIFY_TOKEN = foo.VERIFY_TOKEN
bot = Bot(ACCESS_TOKEN)

# Database config
application.config["MONGO_URI"] = foo.MONGO_URI
mongo = PyMongo(application)

db_operations = mongo.db.user

db_collections = {}

db_collections['IamLoved'] = mongo.db.IamLoved
db_collections['IamOk'] = mongo.db.IamOk
db_collections['IamSafe'] = mongo.db.IamSafe
db_collections['LaborAndDelivery'] = mongo.db.LaborAndDelivery
db_collections['LetsDoThis'] = mongo.db.LetsDoThis


def verify_fb_token(token_sent):
    # take token sent by facebook and verify it matches the verify token you sent
    # if they match, allow the request, else return an error
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


def update_user(user):
    for collection_name in db_collections:
        verses = db_collections[collection_name].find()
        for verse in verses:
            _update = {
                "$set": {
                    f"{collection_name}.{verse['_id']}.audio_url": "Foobar",
                    f"{collection_name}.{verse['_id']}.ReferenceLf": verse['ReferenceLf'],
                }
            }
            db_operations.update_one(user, _update)


def listen_to_playlist(user):
    collection_name = user['ref']
    recordings = user[collection_name]
    audio_url = ""
    files = []
    for ref in recordings:
        audio_url = recordings[ref]['audio_url']
        if audio_url != "Foobar":
            r = requests.get(audio_url, allow_redirects=True)
            file = audio_url.split("/")[-1].split("?")[0]
            with open(f"./{file}",'wb') as f:
                f.write(r.content)
            files.append(AudioSegment.from_file(f"./{file}", "mp4"))

    playlist = files[0]
    for i in range(1, len(files)):
        playlist = playlist + files[i]
    
    playlist.export(f"{collection_name}.mp3", "mp3")

    file_mime_type, _ = mimetypes.guess_type(f"{collection_name}.mp3")

    # Uploading to S3 bucket
    s3_resource = boto3.resource('s3')
    bucket = s3_resource.Bucket("verse-recordings")
    bucket.upload_file(Filename=f"{collection_name}.mp3", Key=f"{user['_id']}/{collection_name}.mp3", ExtraArgs={'ContentType': file_mime_type})

    # Public URL of the recording
    audio_url = f"https://verse-recordings.s3.ap-south-1.amazonaws.com/{user['_id']}/{collection_name}.mp3"

    # Sending the stitched version of all the recordings
    bot.send_audio_url(recipient_id=user['_id'], audio_url=audio_url)


def create_schedule(user):
    buttons = [
        {
            "type":"postback",
            "title":"Daily",
            "payload": "Daily"
        },
        {
            "type":"postback",
            "title": "Two times a day",
            "payload": "Two times a day"
        },
        {
            "type":"postback",
            "title": "Three times a day",
            "payload": "Three times a day"
        }
    ]
    bot.send_button_message(recipient_id=user["_id"], text="Select a schedule", buttons=buttons)


def read_all_verses(user):
    entries = db_collections[user['ref']].find()
    i = 1
    for entry in entries:
        verse = f"\"{entry['verse']}\"\n{entry['ReferenceLf']}, {entry['version']}"
        bot.send_text_message(recipient_id=user['_id'], message=verse)
        if i == 10:
            break
        i += 1


@application.route("/list")
def foo():
    entries = list(db_collections["IamOk"].find())
    verses = [entry['verse'] for entry in entries]
    # print(verses)
    return "success"


# We will receive messages that Facebook sends to the bot at this endpoint
@application.route("/webhooks/facebook/webhook", methods=['GET', 'POST'])
def receive_message():
    if request.method == 'GET':
        """Before allowing people to message your bot, Facebook has implemented a verify token
        that confirms all requests that your bot receives came from Facebook."""
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    # if the request was not get, it must be POST and we can just proceed with sending a message back to user
    else:
        # get whatever message a user sent the bot
        output = request.get_json()
        for event in output['entry']:
            messaging = event['messaging']
            for message in messaging:
                # Upserting the user
                recipient_id = message['sender']['id']
                user = db_operations.find_one({'_id': int(recipient_id)})
                if user is None:
                    try:    
                        new_user = {'_id': int(recipient_id), 'prevBotMsg': "Foo", "schedule": "None"}
                        db_operations.insert_one(new_user)
                        user = db_operations.find_one({'_id': int(recipient_id)})
                        update_user(user)
                    except DuplicateKeyError:
                        pass
                try:
                    prevBotMsg = user['prevBotMsg']
                except:
                    prevBotMsg = "Foo"

                if message.get('postback'):
                    postback = message['postback']

                    if postback.get("referral"):
                        # Are there any Messenger ref values in the query parameter
                        if postback['referral'].get('ref'):
                            ref = postback['referral']['ref']
                            # print(ref)
                            updateUser = {"$set": {"ref": ref}}
                            db_operations.update_one(user, updateUser)

                            # Getting the sender's name
                            r = requests.get('https://graph.facebook.com/{}?fields=first_name,last_name,profile_pic&access_token={}'.format(recipient_id, ACCESS_TOKEN)).json()
                            try:
                                first_name = r['first_name']
                                last_name = r['last_name']
                                msg = f"Welcome {first_name} {last_name}!"
                                updateUser = {"$set": {"name": f"{first_name} {last_name}"}}
                                db_operations.update_one(user, updateUser)
                            except KeyError:
                                msg = "Welcome!"

                            # Greeting the user
                            bot.send_text_message(recipient_id=recipient_id, message=msg)

                            # Sending an image corresponding to the ref value
                            imageURLs = {
                                "IamLoved": "https://i.ibb.co/5Ljc7vX/Whats-App-Image-2021-07-19-at-15-49-57.jpg",
                                "IamOk": "https://i.ibb.co/N2mjWC0/Whats-App-Image-2021-07-31-at-11-19-36-AM.jpg",
                                "LetsDoThis": "https://i.ibb.co/5KwPGs4/Whats-App-Image-2021-07-31-at-11-18-10-AM.jpg"
                            }
                            bot.send_image_url(recipient_id=recipient_id, image_url=imageURLs[ref])
                            bot.send_text_message(recipient_id=recipient_id, message="Which verse did you read today?")

                            updateUser = {"$set": {"prevBotMsg": "Which verse did you read today?"}}
                            db_operations.update_one(user, updateUser)
                    else:
                        postbackTitle = message['postback']['title']
                        if postbackTitle == "Record":
                            updateUser = {"$set": {"prevBotMsg": "Nice! Send your recording of this verse"}}
                            db_operations.update_one(user, updateUser)

                            bot.send_text_message(recipient_id=recipient_id, message="Nice! Send your recording of this verse")
                        
                        elif postbackTitle == "Listen to Playlist":
                            listen_to_playlist(user)

                        elif postbackTitle == "Create Schedule":
                            create_schedule(user)
                        
                        elif postbackTitle == "Daily":
                            updateUser = {
                                "$set": {
                                    "schedule": "Daily"
                                }
                            }
                            db_operations.update_one(user, updateUser)
                            bot.send_text_message(recipient_id=recipient_id, message="You'll get a playlist reminder everyday at 12 PM")
                        
                        elif postbackTitle == "Two times a day":
                            updateUser = {
                                "$set": {
                                    "schedule": "2"
                                }
                            }
                            db_operations.update_one(user, updateUser)
                            bot.send_text_message(recipient_id=recipient_id, message="You'll get a playlist reminder everyday at 6 AM and 6 PM")
                        
                        elif postbackTitle == "Three times a day":
                            updateUser = {
                                "$set": {
                                    "schedule": "3"
                                }
                            }
                            db_operations.update_one(user, updateUser)
                            bot.send_text_message(recipient_id=recipient_id, message="You'll get a playlist reminder everyday at 6 AM, 12 PM, and 6 PM")
                        
                        elif postbackTitle == "Read All Verses":
                            read_all_verses(user)
                    
                elif message.get('message'):
                    userMessage = message['message']
                    # User enters a verse
                    if "Which verse did you read today" in prevBotMsg:
                        for collection_name in db_collections:
                            enteredVerse = userMessage['text']
                            verse_doc = db_collections[collection_name].find_one({
                                "$or":
                                [
                                    {
                                        'ReferenceSf':{ '$regex':f'^{enteredVerse}$', "$options":"i"}
                                    },
                                    {
                                        'ReferenceLf': { '$regex':f'^{enteredVerse}$', "$options":"i"}
                                    }
                                ]
                            })

                            if verse_doc is not None:
                                verse_doc['ref'] = collection_name
                                break

                        # print(verse_doc)

                        if verse_doc is not None:
                            verse = f"\"{verse_doc['verse']}\"\n{verse_doc['ReferenceLf']}, {verse_doc['version']}"

                            bot.send_text_message(recipient_id=recipient_id, message=verse)

                            buttons = [
                                {
                                    "type":"postback",
                                    "title":"Record",
                                    "payload": "Record"
                                },
                                {
                                    "type":"postback",
                                    "title": "Hear an example",
                                    "payload": "Example"
                                }
                            ]
                            updateUser = {"$set": {"verse_id": verse_doc["_id"], "ref": verse_doc['ref']}}
                            db_operations.update_one(user, updateUser)

                            r = bot.send_button_message(recipient_id=recipient_id, text="Record this verse and your declaration", buttons=buttons)
                            # print(r)

                    elif "Nice!" in prevBotMsg:
                        if userMessage.get("attachments"):
                            audios = userMessage['attachments']
                            for audio in audios:
                                if audio.get("payload"):
                                    url = audio["payload"]["url"]
                                    updateUser = {
                                        "$set": {
                                            f"{user['ref']}.{user['verse_id']}.audio_url": url
                                        }
                                    }
                                    db_operations.update_one(user, updateUser)
                                    modified_collection_name = {
                                        "IamLoved": "I am Loved",
                                        "IamOk": "I am Ok",
                                        "IamSafe": "I am Safe",
                                        "LaborAndDelivery": "Labor And Delivery",
                                        "LetsDoThis": "Let's Do This"
                                    }
                                    msg = f"Added to {modified_collection_name[user['ref']]} playlist"
                                    bot.send_text_message(recipient_id=recipient_id, message=msg)

                                    buttons = [
                                        {
                                            "type":"postback",
                                            "title":"Listen to Playlist",
                                            "payload": "Listen to Playlist"
                                        },
                                        {
                                            "type":"postback",
                                            "title": "Create Schedule",
                                            "payload": "Create Schedule"
                                        },
                                        {
                                            "type":"postback",
                                            "title": "Read All Verses",
                                            "payload": "Read All Verses"
                                        }
                                    ]
                                    bot.send_button_message(recipient_id=recipient_id, text="Select an option", buttons=buttons)
    return "Message Processed"


if __name__ == "__main__":
    application.run(port=5005)
