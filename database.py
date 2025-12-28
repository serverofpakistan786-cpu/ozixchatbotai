from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class MongoDB:
    def __init__(self):
        self.MONGO_URI = os.getenv("MONGO_URI")
        self.client = MongoClient(self.MONGO_URI)
        self.db = self.client.telegram_bot
        self.users = self.db.users
        self.conversations = self.db.conversations
        self.groups = self.db.groups
    
    def get_user(self, user_id: int):
        """Get user from database"""
        return self.users.find_one({"user_id": user_id})
    
    def create_user(self, user_data: dict):
        """Create new user"""
        user_data["created_at"] = datetime.now()
        user_data["updated_at"] = datetime.now()
        self.users.insert_one(user_data)
    
    def update_user(self, user_id: int, update_data: dict):
        """Update user data"""
        update_data["updated_at"] = datetime.now()
        self.users.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
    
    def add_conversation(self, user_id: int, role: str, message: str):
        """Save conversation history"""
        self.conversations.insert_one({
            "user_id": user_id,
            "role": role,
            "message": message,
            "timestamp": datetime.now()
        })
    
    def get_conversation_history(self, user_id: int, limit: int = 10):
        """Get last N conversations"""
        return list(self.conversations.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit))
    
    def get_all_users(self):
        """Get all users count"""
        return self.users.count_documents({})
    
    def add_group_subscription(self, user_id: int, group_type: str):
        """Record group join"""
        self.groups.update_one(
            {"user_id": user_id},
            {"$set": {f"joined_{group_type}": True, "joined_at": datetime.now()}},
            upsert=True
        )
