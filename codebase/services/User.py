from backend.models.User import UserModel
from backend.lib.Mongo import MongoDBConnection
import datetime
import pymongo
from bson.objectid import ObjectId

from typing import List

class User:
    # Function to create user, inputs are what we extract out of next-auth
    @staticmethod
    def create_user(user_info: dict):
        # Import here to avoid circular import
        from backend.middleware.user.User import UserMiddleware
        
        # Apply middleware validation
        @UserMiddleware.validate_user_input
        def _create_user_with_validation(user_info: dict):
            db = MongoDBConnection.get_db()
            user_data = {
                "username": user_info["email"].split("@")[0],
                "first_name": user_info["first_name"],
                "last_name": user_info["last_name"],
                "profile_picture": user_info["profile_picture"],
                "email": user_info["email"],
                "store": None,
                "subscription": None,
                "created_at": datetime.datetime.now(),
                "customer": None,
                "affiliate": None,
                "phone_number": "",
                "favorites": [],
                "transactions": [],
                "purchased_automations": [],
                "search_history": [],
                "beta_tester": False,
                "referred": {
                    "is_referred": True if user_info["affilate_code"] else False,
                    "affilate_code": user_info["affilate_code"] if user_info["affilate_code"] else None
                }
            }

            # Insert the user into the database
            result = db["users"].insert_one(user_data)
            user_data["_id"] = result.inserted_id
            
            return user_data
        
        return _create_user_with_validation(user_info)
    
    # Checks if a user exits, can lookup by user id or email address, returns True or False
    @staticmethod
    def exists(user_id: str = None, email: str = None):
        user = None
        db = MongoDBConnection.get_db()
        if user_id:
            user = db["users"].find_one({"_id": ObjectId(user_id)})
            if not user or len(user) == 0:
                return False
        
        if email:
            user = db["users"].find_one({"email": email})
            if not user or len(user) == 0:
                return False
            
        if not user: 
            return False
        
        return True

    @staticmethod
    def get_user_client_info(user_id: str) -> dict:
        """Get client-safe user information"""
        db = MongoDBConnection.get_db()
        user = db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            return None
        
        user_model = UserModel(**user)
        user_data = {**user_model.model_dump()}
        
        # Filter out sensitive information for client-side use
        client_safe_data = {
            "id": user_data.get("id"),
            "username": user_data.get("username"),
            "first_name": user_data.get("first_name"),
            "last_name": user_data.get("last_name"),
            "profile_picture": user_data.get("profile_picture"),
            "email": user_data.get("email"),
            "phone_number": user_data.get("phone_number"),
            "favorites": user_data.get("favorites"),
            "created_at": user_data.get("created_at")
        }

        return client_safe_data

    @staticmethod
    def get_user_info(user_id: str) -> dict:
        """Returns same data that goes into mongodb"""
        db = MongoDBConnection.get_db()
        user = db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            return None
        
        user_model = UserModel(**user)
        return {**user_model.model_dump()}

    @staticmethod
    def get_user_server_info(user_id: str) -> dict:
        """Get the full information corresponding to a user, including all of their information relating to their id references
        CONTAINS SENSITIVE INFORMATION, ONLY RUN ON THE SERVER SIDE"""
        db = MongoDBConnection.get_db()
        user = db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            return None
        
        user_model = UserModel(**user)
        user_data = {**user_model.model_dump()}
        store_data = None
        invoices = []
        subscription_data = None
        customer_data = None
        affiliate_data = None
        transactions = []
        purchased_automations = []

        # Get the store data
        if user_data.get("store"):
            store_data = db["stores"].find_one({"_id": ObjectId(user_data["store"])})

        # Get the invoices data
        if len(user_data.get("invoices", [])) > 0:
            for invoice_id in user_data["invoices"]:
                invoice_data = db["invoices"].find_one({"_id": ObjectId(invoice_id)})
                if invoice_data:
                    invoices.append(invoice_data)

        # Get the subscription data
        if user_data.get("subscription"):
            subscription_data = db["subscriptions"].find_one({"_id": ObjectId(user_data["subscription"])})

        # Get the customer data
        if user_data.get("customer"):
            customer_data = db["customers"].find_one({"_id": ObjectId(user_data["customer"])})

        # Get the affiliate data
        if user_data.get("affiliate"):
            affiliate_data = db["affiliates"].find_one({"_id": ObjectId(user_data["affiliate"])})

        # Get the transactions data
        if len(user_data.get("transactions", [])) > 0:
            transactions = user_data["transactions"]  # Transactions are stored inline

        # Get purchased automations
        if len(user_data.get("purchased_automations", [])) > 0:
            for product_id in user_data["purchased_automations"]:
                product_info = db["products"].find_one({"_id": ObjectId(product_id)})
                if product_info:
                    purchased_automations.append(product_info)

        return {
            **user_data, 
            "store": store_data, 
            "invoices": invoices, 
            "subscription": subscription_data, 
            "customer": customer_data, 
            "affiliate": affiliate_data, 
            "transactions": transactions, 
            "purchased_automations": purchased_automations
        }
        
    @staticmethod
    def update_user_info(user_id: str, update_data: dict):
        """Update user information"""
        # Import here to avoid circular import
        from backend.middleware.user.User import UserMiddleware
        
        @UserMiddleware.validate_user_exists
        def _update_user_with_validation(user_id: str, update_data: dict):
            db = MongoDBConnection.get_db()
            
            # Remove any information that should not be updated
            update_data.pop("_id", None)
            update_data.pop("created_at", None)
            update_data.pop("email", None)  # Email should be immutable for security
            update_data.pop("username", None)  # Username should be immutable
            
            # Update in database using constant time operation
            result = db["users"].update_one(
                {"_id": ObjectId(user_id)}, 
                {"$set": update_data}
            )
            
            return result.modified_count > 0
        
        return _update_user_with_validation(user_id, update_data)

    @staticmethod
    def delete_user_info(user_id: str):
        """Delete user"""
        # Import here to avoid circular import
        from backend.middleware.user.User import UserMiddleware
        
        @UserMiddleware.validate_user_exists
        def _delete_user_with_validation(user_id: str):
            db = MongoDBConnection.get_db()
            result = db["users"].delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        
        return _delete_user_with_validation(user_id)
    
    @staticmethod
    def has_active_subscription(user_id):
        # Import here to avoid circular import
        from backend.services.transactions.Subscriptions import Subscription
        
        if not User.exists(user_id):
            return False
        
        subscription_id = User.get_user_info(user_id)["subscription"]

        if not Subscription.exists(subscription_id):
            return False
        
        subscription_active = Subscription.get(subscription_id)["active"]

        return subscription_active

    # ===== MARKETPLACE-SPECIFIC FUNCTIONS =====

    @staticmethod
    def add_to_favorites(user_id: str, product_id: str) -> bool:
        """Add a product to user's favorites list"""
        pass

    @staticmethod
    def remove_from_favorites(user_id: str, product_id: str) -> bool:
        """Remove a product from user's favorites list"""
        pass

    @staticmethod
    def get_favorites(user_id: str, limit: int = 20, skip: int = 0) -> List[dict]:
        """Get user's favorite products with pagination"""
        pass

    @staticmethod
    def add_purchased_automation(user_id: str, product_id: str, transaction_id: str) -> bool:
        """Add an automation to user's purchased list"""
        pass

    @staticmethod
    def get_purchase_history(user_id: str, limit: int = 20, skip: int = 0) -> List[dict]:
        """Get user's purchase history with product details"""
        pass

    @staticmethod
    def has_purchased_product(user_id: str, product_id: str) -> bool:
        """Check if user has already purchased a specific product"""
        pass

    @staticmethod
    def calculate_seller_reputation(user_id: str) -> dict:
        """Calculate seller reputation metrics based on sales, reviews, ratings"""
        pass

    @staticmethod
    def get_seller_metrics(user_id: str) -> dict:
        """Get comprehensive seller metrics (sales, revenue, ratings, reviews)"""
        pass

    @staticmethod
    def report_user(reporter_id: str, reported_user_id: str, reason: str, details: str = "") -> str:
        """Report a user for policy violations"""
        pass

    @staticmethod
    def verify_seller_identity(user_id: str, verification_data: dict) -> bool:
        """Verify seller identity for premium features"""
        pass

    @staticmethod
    def get_recommended_users(user_id: str, limit: int = 10) -> List[dict]:
        """Get recommended sellers/users based on user preferences"""
        pass

    @staticmethod
    def update_user_analytics(user_id: str, event_type: str, metadata: dict = None) -> bool:
        """Track user behavior for analytics and recommendations"""
        pass

    @staticmethod
    def get_user_activity_feed(user_id: str, limit: int = 20, skip: int = 0) -> List[dict]:
        """Get user's activity feed (purchases, likes, follows, etc.)"""
        pass
        