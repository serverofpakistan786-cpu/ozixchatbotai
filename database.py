from pymongo import MongoClient
from datetime import datetime
import os

class MongoDB:
    def __init__(self):
        self.MONGO_URI = os.getenv("MONGO_URI")
        if not self.MONGO_URI:
            raise ValueError("MONGO_URI not found in environment variables")
        
        self.client = MongoClient(self.MONGO_URI, serverSelectionTimeoutMS=5000)
        self.db = self.client.ayesha_bot
        self.users = self.db.users
    
    def create_user(self, user_data):
        """Create new user in database"""
        try:
            user_data["created_at"] = datetime.now()
            self.users.update_one(
                {"user_id": user_data["user_id"]},
                {"$set": user_data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Database error: {e}")
            return False
    
    def get_user(self, user_id):
        """Get user from database"""
        return self.users.find_one({"user_id": user_id})
    
    def get_all_users_count(self):
        """Get total users count"""
        return self.users.count_documents({})
