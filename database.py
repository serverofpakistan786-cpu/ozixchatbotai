from pymongo import MongoClient
from datetime import datetime
import os

class MongoDB:
    def __init__(self):
        self.MONGO_URI = os.getenv("MONGO_URI")
        self.client = MongoClient(self.MONGO_URI)
        self.db = self.client.ayesha_bot
        self.users = self.db.users
    
    def create_user(self, user_data):
        try:
            self.users.update_one(
                {"user_id": user_data["user_id"]},
                {"$set": user_data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Database error: {e}")
            return False
