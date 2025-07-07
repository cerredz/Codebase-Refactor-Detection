from backend.lib.Mongo import MongoDBConnection
from backend.services.User import User
from bson.objectid import ObjectId
from backend.models.Store import StoreModel
from backend.errors.User import UserAlreadyHasStoreError, UserNotFoundError
from backend.middleware.Store.Store import StoreMiddleware
import datetime
from typing import List

class Store:
    
    # Creates a store object and links it to a user
    @staticmethod
    @StoreMiddleware.validate_user_doesnt_have_store
    @StoreMiddleware.generate_store_link
    def create_store(user_id, store_info: dict, store_link: str = None):
        if not User.exists(user_id=user_id):
            raise UserNotFoundError
        
        user = User.get_user_info(user_id=user_id)
        
        db = MongoDBConnection.get_db()

        store_data = {
            "logo": store_info.get("logo", ""),
            "name": store_info.get("name", ""),
            "description": store_info.get("description", ""),
            "store_link": store_link,
            "user_id": user_id,
            "products": [],
            "num_products": 0,
            "socials": {},
            "email": user.get("email", ""),
            "created_at": datetime.datetime.now(),
            "sales": 0,
            "total_revenue": 0,
            "views": 0,
            "saved": 0,
            "tags": store_info.get("tags", []),
            "location": store_info.get("location", ""),
            "website": store_info.get("website", ""),
            "balance": 0,
            "recent_sales": []
        }

        # Insert the store into the database
        result = db["stores"].insert_one(store_data)
        
        if not result.acknowledged:
            raise Exception("Error writing to database when adding store to the Stores collection.")
        
        store_id = result.inserted_id
        
        # Update the user document to link to the new store
        db["users"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"store": str(store_id)}}
        )
        
        # Return the newly created store ID and store link
        return str(store_id), str(store_link)
    
    @staticmethod
    def exists(store_id):
        db = MongoDBConnection.get_db()
        store = db["stores"].find_one({"_id": ObjectId(store_id)})
        if not store or len(store) == 0:
            return False
        return True
    
    @staticmethod
    def get_store_info(store_id: str) -> dict:
        """Returns same data that goes into mongodb"""
        db = MongoDBConnection.get_db()
        store = db["stores"].find_one({"_id": ObjectId(store_id)})
        if not store:
            return None
        
        store_model = StoreModel(**store)
        return store_model

    @staticmethod
    def get_store_client_info(store_id: str) -> dict:
        """Safe store data for client-side use"""
        db = MongoDBConnection.get_db()
        store = db["stores"].find_one({"_id": ObjectId(store_id)})
        if not store:
            return None
        
        store_model = StoreModel(**store)
        store_data = {**store_model.model_dump()}
        
        # Filter out sensitive information for client-side use
        client_safe_data = {
            "_id": store_data.get("_id"),
            "logo": store_data.get("logo"),
            "name": store_data.get("name"),
            "description": store_data.get("description"),
            "socials": store_data.get("socials"),
            "email": store_data.get("email"),
            "created_at": store_data.get("created_at"),
            "views": store_data.get("views"),
            "saved": store_data.get("saved"),
            "tags": store_data.get("tags"),
            "location": store_data.get("location"),
            "website": store_data.get("website"),
            "num_products": store_data.get("num_products")
        }

        return client_safe_data

    @staticmethod
    def get_store_server_info(store_id: str) -> dict:
        """Full store data with related user info - SERVER SIDE ONLY"""
        db = MongoDBConnection.get_db()
        store = db["stores"].find_one({"_id": ObjectId(store_id)})
        if not store:
            return None
        
        store_model = StoreModel(**store)
        store_data = {**store_model.model_dump()}
        user_data = None

        # Get the user data
        user_id = store_data.get("user_id")
        if user_id:
            user_data = db["users"].find_one({"_id": ObjectId(user_id)})

        return {
            **store_data,
            "user": user_data
        }
    
    @staticmethod
    def get_store_profile(store_id: str):
        """Gets store data combined with public user info - useful for profile pages"""
        store_info = Store.get_store_client_info(store_id)
        if not store_info:
            return None
        
        # Get user_id from store data
        db = MongoDBConnection.get_db()
        store = db["stores"].find_one({"_id": ObjectId(store_id)})
        if not store:
            return None
        
        user_id = store.get("user_id")
        user_info = User.get_user_client_info(user_id)
        
        return {
            "store": store_info,
            "user": user_info
        }
    
    @staticmethod
    @StoreMiddleware.validate_store_exists
    @StoreMiddleware.validate_user_store_relationship
    def update_store_info(user_id: str, store_id: str, update_info: dict):
        """Update store information"""
        db = MongoDBConnection.get_db()
         # Remove any fields that shouldn't be updated directly
        update_info.pop("_id", None)
        update_info.pop("user_id", None)
        update_info.pop("created_at", None)
        update_info.pop("store_link", None)
        
        # Update in database using constant time operation
        result = db["stores"].update_one(
            {"_id": ObjectId(store_id)}, 
            {"$set": update_info}
        )
        
        return result.modified_count > 0
    
    @staticmethod
    def delete_store_info(store_id: str):
        """Delete store and unlink from user"""
        db = MongoDBConnection.get_db()
        
        # Get store to find user_id
        store = db["stores"].find_one({"_id": ObjectId(store_id)})
        if not store:
            return False
        
        user_id = store.get("user_id")
        
        # Delete the store
        result = db["stores"].delete_one({"_id": ObjectId(store_id)})
        
        if result.deleted_count > 0 and user_id:
            # Unlink store from user
            db["users"].update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"store": None}}
            )
        
        return result.deleted_count > 0

    @staticmethod
    def increment_views(store_id: str):
        """Constant time view increment"""
        db = MongoDBConnection.get_db()
        result = db["stores"].update_one(
            {"_id": ObjectId(store_id)},
            {"$inc": {"views": 1}}
        )
        return result.modified_count > 0

    @staticmethod
    def increment_saved(store_id: str):
        """Constant time saved increment"""
        db = MongoDBConnection.get_db()
        result = db["stores"].update_one(
            {"_id": ObjectId(store_id)},
            {"$inc": {"saved": 1}}
        )
        return result.modified_count > 0

    @staticmethod
    def get_stores_by_user(user_id):
        """Get store for a specific user (should only be one)"""
        db = MongoDBConnection.get_db()
        store = db["stores"].find_one({"user_id": user_id})
        return store

    @staticmethod
    def search_stores(query, limit=20, skip=0):
        """Search stores by name, description, tags"""
        db = MongoDBConnection.get_db()
        stores = db["stores"].find({
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"tags": {"$in": [query]}}
            ]
        }).skip(skip).limit(limit).sort("views", -1)
        
        return list(stores)

    # ===== MARKETPLACE-SPECIFIC FUNCTIONS =====

    @staticmethod
    def follow_store(user_id: str, store_id: str) -> bool:
        """Follow a store for updates"""
        pass

    @staticmethod
    def unfollow_store(user_id: str, store_id: str) -> bool:
        """Unfollow a store"""
        pass

    @staticmethod
    def get_store_followers(store_id: str, limit: int = 20, skip: int = 0) -> List[dict]:
        """Get list of users following this store"""
        pass

    @staticmethod
    def get_followed_stores(user_id: str, limit: int = 20, skip: int = 0) -> List[dict]:
        """Get stores that user is following"""
        pass

    @staticmethod
    def get_store_analytics(store_id: str, time_period: str = "30d") -> dict:
        """Get comprehensive store analytics (sales, views, revenue, top products)"""
        pass

    @staticmethod
    def get_trending_stores(limit: int = 20, time_period: str = "7d") -> List[dict]:
        """Get trending stores based on growth metrics"""
        pass

    @staticmethod
    def get_featured_stores(limit: int = 20) -> List[dict]:
        """Get featured/promoted stores"""
        pass

    @staticmethod
    def verify_store(store_id: str, verification_type: str, verifier_id: str) -> bool:
        """Verify store (badge, premium status, etc.)"""
        pass

    @staticmethod
    def get_store_performance_metrics(store_id: str) -> dict:
        """Get detailed performance metrics for store owner dashboard"""
        pass

    @staticmethod
    def update_store_balance(store_id: str, amount: float, transaction_type: str) -> bool:
        """Update store balance (earnings, payouts, fees)"""
        pass

    @staticmethod
    def calculate_store_ranking_score(store_id: str) -> float:
        """Calculate store quality/ranking score"""
        pass

    @staticmethod
    def get_stores_by_category(category: str, limit: int = 20, skip: int = 0) -> List[dict]:
        """Get stores filtered by category/specialization"""
        pass

    @staticmethod
    def get_recommended_stores(user_id: str, limit: int = 10) -> List[dict]:
        """Get recommended stores for user"""
        pass

    @staticmethod
    def flag_store(store_id: str, flagger_id: str, reason: str, details: str = "") -> str:
        """Flag store for policy violations"""
        pass

    @staticmethod
    def moderate_store(store_id: str, action: str, moderator_id: str, reason: str = "") -> bool:
        """Moderate stores (approve, suspend, ban)"""
        pass

    @staticmethod
    def get_store_competitors(store_id: str, limit: int = 10) -> List[dict]:
        """Get similar/competing stores"""
        pass

    @staticmethod
    def update_store_social_links(store_id: str, social_links: dict) -> bool:
        """Update store's social media links"""
        pass

    @staticmethod
    def get_store_activity_feed(store_id: str, limit: int = 20, skip: int = 0) -> List[dict]:
        """Get store's recent activity (new products, sales, etc.)"""
        pass

    @staticmethod
    def schedule_store_payout(store_id: str, amount: float, payout_date: datetime = None) -> str:
        """Schedule automatic payout for store earnings"""
        pass

    @staticmethod
    def get_top_selling_stores(category: str = None, time_period: str = "30d", limit: int = 20) -> List[dict]:
        """Get top selling stores by revenue/sales volume"""
        pass






    




