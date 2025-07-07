from backend.lib.Mongo import MongoDBConnection
from backend.services.User import User
from backend.services.Store import Store
from backend.models.Product import ProductModel
from bson.objectid import ObjectId
import datetime
from typing import List, Tuple
from backend.middleware.product.Product import ProductMiddleware
from backend.middleware.Store.Store import StoreMiddleware
import urllib.parse

class Product:
    
    # Creates a new product and links it to a user and store
    @staticmethod
    @ProductMiddleware.validate_product_input
    @ProductMiddleware.validate_product_title
    @StoreMiddleware.validate_store_exists
    @StoreMiddleware.validate_user_store_relationship
    def create_product(user_id: str, store_id: str, product_info: dict):
        
        # Create the product document
        db = MongoDBConnection.get_db()
        product_link = f"products/{urllib.parse.quote(product_info['title'])}"
        
        product_data = {
            "title": product_info["title"],
            "description": product_info["description"],
            "user_id": user_id,
            "store_id": store_id,
            "username": product_info["username"],
            "about": product_info["about"],
            "features": product_info["features"],
            "tags": product_info["tags"],
            "created_at": datetime.datetime.now(),
            "views": 0,
            "sales": 0,
            "revenue": 0.0,
            "price": 0,
            "platform": product_info["platform"] or "",
            "instructions": product_info["instructions"],
            "supported_triggers": product_info["suppored_triggers"] or [],
            "pictures": product_info["pictures"] or [],
            "reviews": [],
            "review_count": 0,
            "workflow_id": "",
            "instruction_links": product_info["instruction_links"] or [],
            "product_link": product_link
        }
        
        # Insert the product into the database
        result = db["products"].insert_one(product_data)

        if not result.acknowledged:
            raise Exception("Error writing to database when adding product to the Products collection.")

        # Add product to store's products list using constant time operation
        db["stores"].update_one(
            {"_id": ObjectId(store_id)},
            {
                "$push": {"products": str(result.inserted_id)},
                "$inc": {"num_products": 1}
            }
        )

        product_id = str(result.inserted_id)
        
        # Return the newly created product ID and product link
        return product_id, product_link

    # Checks if a product exists or not
    @staticmethod
    def exists(product_id):
        db = MongoDBConnection.get_db()
        product = db["products"].find_one({"_id": ObjectId(product_id)})
        if not product or len(product) == 0:
            return False
        
        return True

    @staticmethod
    @ProductMiddleware.validate_product_exists
    def get_product_client_info(product_id: str) -> dict:
        """Get client-safe product information"""
        db = MongoDBConnection.get_db()
        product = db["products"].find_one({"_id": ObjectId(product_id)})
        if not product:
            return None
        
        product_model = ProductModel(**product)
        product_data = {**product_model.model_dump()}
        
        # Filter out sensitive information for client-side use
        client_safe_data = {
            "id": product_data.get("id"),
            "title": product_data.get("title"),
            "description": product_data.get("description"),
            "username": product_data.get("username"),
            "about": product_data.get("about"),
            "features": product_data.get("features"),
            "tags": product_data.get("tags"),
            "created_at": product_data.get("created_at"),
            "views": product_data.get("views"),
            "price": product_data.get("price"),
            "platform": product_data.get("platform"),
            "pictures": product_data.get("pictures"),
            "reviews": product_data.get("reviews"),
            "review_count": product_data.get("review_count")
        }

        return client_safe_data

    @staticmethod
    @ProductMiddleware.validate_product_exists
    def get_product_info(product_id: str) -> dict:
        """Returns same data that goes into mongodb"""
        db = MongoDBConnection.get_db()
        product = db["products"].find_one({"_id": ObjectId(product_id)})
        if not product:
            return None
        
        product_model = ProductModel(**product)
        return {**product_model.model_dump()}

    @staticmethod
    @ProductMiddleware.validate_product_exists
    def get_product_server_info(product_id: str) -> dict:
        """Get the full information corresponding to a product, including all related data
        CONTAINS SENSITIVE INFORMATION, ONLY RUN ON THE SERVER SIDE"""
        db = MongoDBConnection.get_db()
        product = db["products"].find_one({"_id": ObjectId(product_id)})
        if not product:
            return None
        
        product_model = ProductModel(**product)
        product_data = {**product_model.model_dump()}
        user_data = None
        store_data = None

        # Get the user data
        if product_data.get("user_id"):
            user_data = db["users"].find_one({"_id": ObjectId(product_data["user_id"])})

        # Get the store data
        if product_data.get("store_id"):
            store_data = db["stores"].find_one({"_id": ObjectId(product_data["store_id"])})

        return {
            **product_data,
            "user": user_data,
            "store": store_data
        }
    
    @staticmethod
    @ProductMiddleware.validate_product_exists
    @ProductMiddleware.validate_product_ownership
    @ProductMiddleware.validate_product_input
    def update_product_info(product_id: str, user_id: str, product_info: dict):
        """Update product information"""
        db = MongoDBConnection.get_db()

        # Remove any information that should not be updated
        product_info.pop("product_link", None)
        product_info.pop("workflow_id", None)
        product_info.pop("user_id", None)
        product_info.pop("created_at", None)
        product_info.pop("username", None)
        product_info.pop("store_id", None)
        
        # Update in database using constant time operation
        result = db["products"].update_one(
            {"_id": ObjectId(product_id)}, 
            {"$set": product_info}
        )
        
        return result.modified_count > 0

    @staticmethod
    @ProductMiddleware.validate_product_exists
    @ProductMiddleware.validate_product_ownership
    @StoreMiddleware.validate_store_exists
    @ProductMiddleware.validate_product_store_relationsip
    @StoreMiddleware.validate_user_store_relationship
    def delete_product_info(product_id: str, user_id: str, store_id: str):
        """Delete product and remove from store"""
        db = MongoDBConnection.get_db()        
        # Delete the product
        result = db["products"].delete_one({"_id": ObjectId(product_id)})
        
        if result.deleted_count > 0 and store_id:
            # Remove product from store's products list and decrement count (constant time)
            db["stores"].update_one(
                {"_id": ObjectId(store_id)},
                {
                    "$pull": {"products": product_id},
                    "$inc": {"num_products": -1}
                }
            )
        
        return result.deleted_count > 0

    @staticmethod
    @ProductMiddleware.validate_product_exists
    def increment_views(product_id: str):
        """Constant time view increment"""
        db = MongoDBConnection.get_db()
        result = db["products"].update_one(
            {"_id": ObjectId(product_id)},
            {"$inc": {"views": 1}}
        )
        return result.modified_count > 0

    @staticmethod
    @ProductMiddleware.validate_product_exists
    def add_sale(product_id: str, sale_amount: float, buyer_user_id: str = None):
        """Add a sale to the product and update store metrics"""
        db = MongoDBConnection.get_db()
        
        # Get product to find store_id
        product = db["products"].find_one({"_id": ObjectId(product_id)})        
        store_id = product.get("store_id")
        
        # Add the sale to the product
        db["products"].update_one(
            {"_id": ObjectId(product_id)},
            {
                "$inc": {
                    "sales": 1,
                    "revenue": sale_amount
                }
            }
        )

        # Update the store's sales
        if store_id:
            db["stores"].update_one(
                {"_id": ObjectId(store_id)},
                {
                    "$inc": {
                        "sales": 1,
                        "total_revenue": sale_amount
                    }
                }
            )

        # Update buyer's purchased automations if buyer_user_id provided
        if buyer_user_id:
            db["users"].update_one(
                {"_id": ObjectId(buyer_user_id)},
                {"$push": {"purchased_automations": product_id}}
            )

    @staticmethod
    @ProductMiddleware.validate_product_exists
    def add_review(product_id: str, rating: int):
        """Constant time review addition"""
        if not (1 <= rating <= 5):
            raise Exception("Rating must be between 1 and 5")
        
        db = MongoDBConnection.get_db()
        result = db["products"].update_one(
            {"_id": ObjectId(product_id)},
            {
                "$push": {"reviews": rating},
                "$inc": {"review_count": 1}
            }
        )
        return result.modified_count > 0
    
    # Static method to get a product
    @staticmethod
    @ProductMiddleware.validate_product_exists
    def get(product_id) -> dict:
        """Get a single product by ID"""
        
        db = MongoDBConnection.get_db()
        product = db["products"].find_one({"_id": ObjectId(product_id)})

        product_model = ProductModel(**product)
        return {**product_model.model_dump()}

    # ===== MARKETPLACE-SPECIFIC FUNCTIONS =====

    @staticmethod
    def add_detailed_review(product_id: str, user_id: str, rating: int, title: str, comment: str, verified_purchase: bool = False) -> str:
        """Add a detailed review with title, comment, and verification status"""
        pass

    @staticmethod
    def get_product_reviews(product_id: str, limit: int = 20, skip: int = 0, sort_by: str = "newest") -> List[dict]:
        """Get product reviews with pagination and sorting options"""
        pass

    @staticmethod
    def moderate_review(review_id: str, action: str, moderator_id: str, reason: str = "") -> bool:
        """Moderate reviews (approve, reject, flag)"""
        pass

    @staticmethod
    def get_trending_products(limit: int = 20, time_period: str = "7d") -> List[dict]:
        """Get trending products based on views, sales, and engagement"""
        pass

    @staticmethod
    def get_featured_products(category: str = None, limit: int = 20) -> List[dict]:
        """Get featured/promoted products"""
        pass

    @staticmethod
    def get_recommended_products(user_id: str, limit: int = 20) -> List[dict]:
        """Get personalized product recommendations for user"""
        pass

    @staticmethod
    def get_similar_products(product_id: str, limit: int = 10) -> List[dict]:
        """Get products similar to given product"""
        pass

    @staticmethod
    def update_product_ranking_score(product_id: str, new_score: float) -> bool:
        """Update product's calculated ranking score"""
        pass

    @staticmethod
    def bulk_update_rankings(product_scores: List[Tuple[str, float]]) -> int:
        """Bulk update product ranking scores for efficiency"""
        pass

    @staticmethod
    def get_products_by_category(category: str, limit: int = 20, skip: int = 0, sort_by: str = "ranking") -> List[dict]:
        """Get products filtered by category with sorting"""
        pass

    @staticmethod
    def get_products_by_price_range(min_price: float, max_price: float, limit: int = 20, skip: int = 0) -> List[dict]:
        """Get products within price range"""
        pass

    @staticmethod
    def get_recently_viewed_products(user_id: str, limit: int = 20) -> List[dict]:
        """Get user's recently viewed products"""
        pass

    @staticmethod
    def track_product_view(product_id: str, user_id: str = None, session_id: str = None) -> bool:
        """Track product view for analytics and recommendations"""
        pass

    @staticmethod
    def flag_product(product_id: str, flagger_id: str, reason: str, details: str = "") -> str:
        """Flag product for policy violations"""
        pass

    @staticmethod
    def moderate_product(product_id: str, action: str, moderator_id: str, reason: str = "") -> bool:
        """Moderate products (approve, reject, suspend)"""
        pass

    @staticmethod
    def clone_product_template(original_product_id: str, new_user_id: str, new_store_id: str) -> str:
        """Clone a product as template (for fork/remix functionality)"""
        pass

    @staticmethod
    def get_product_analytics(product_id: str, time_period: str = "30d") -> dict:
        """Get detailed analytics for a product"""
        pass

    @staticmethod
    def set_product_featured(product_id: str, featured: bool, featured_until: datetime = None) -> bool:
        """Set product as featured/promoted"""
        pass

    @staticmethod
    def get_bestselling_products(category: str = None, time_period: str = "30d", limit: int = 20) -> List[dict]:
        """Get best-selling products by sales volume"""
        pass

    @staticmethod
    def get_highest_rated_products(category: str = None, min_reviews: int = 5, limit: int = 20) -> List[dict]:
        """Get highest rated products with minimum review threshold"""
        pass

    @staticmethod
    def update_product_tags(product_id: str, tags: List[str], auto_generated: bool = False) -> bool:
        """Update product tags (manual or auto-generated)"""
        pass

    @staticmethod
    def get_products_needing_review(limit: int = 50) -> List[dict]:
        """Get products that need manual review/moderation"""
        pass
