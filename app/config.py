import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'noobshehe'
    MONGO_DBNAME = os.environ.get('MONGO_DBNAME') or 'notifications'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/notifications'
    VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY')
    VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY') or 'SOz4qDUZaEUp1PapnoK-PMSGK5zr_rfzjuFH8JLijLk'
    VAPID_CLAIMS = {"sub": "mailto:test@test.in"}
