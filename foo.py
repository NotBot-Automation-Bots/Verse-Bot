import os


ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
VERIFY_TOKEN = "abc"
# MONGO_URI = "mongodb://localhost:27017/FbMessenger?retryWrites=true&w=majority"
MONGO_URI = os.getenv("MONGO_URI")

# AWS_ACCESS_KEY_ID = ""
# AWS_SECRET_ACCESS_KEY = ""
# S3_BUCKET_NAME = "verse-recordings"
# S3_URL_EXPIRE_AFTER = 7 * 24 * 60 * 60
