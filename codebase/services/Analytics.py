from backend.middleware.user.User import UserMiddleware
from backend.services.User import User
from backend.services.Store import Store
from backend.errors.User import UserNoSubscriptionError
from backend.lib.Mongo import MongoDBConnection
import datetime
from bson import ObjectId
import pymongo
from typing import List

class Analytics:
    
    @staticmethod
    @UserMiddleware.validate_user_exists
    def get_user_analytics(user_id: str, user_tier: str) -> dict:
        match user_tier:
            case "emerald":
                return Analytics.get_emerald_analytics(user_id)
            case "diamond":
                return Analytics.get_diamond_analytics(user_id)
            case "enterprise":
                return Analytics.get_enterprise_analytics(user_id)
            case _:
                raise UserNoSubscriptionError()
                


    @staticmethod
    def get_emerald_analytics(user_id: str) -> dict:
        ''' Emerald Analytics, most basic analytics. '''
        user = User.get_user_info(user_id)
        store = Store.get_store_info(user.get("store"))

        # Get general store stats
        total_sales = store.get("sales", 0)
        total_rev = store.get("total_revenue", 0.0)
        num_products = store.get("num_products", 0)

        db = MongoDBConnection.get_db()

        # Get all products for this store
        product_object_ids = [ObjectId(doc_id) for doc_id in store.get("products", [])]
        
        if not product_object_ids:
            # Return empty analytics if no products
            return {
                "total_sales": 0,
                "total_revenue": 0.0,
                "total_views": 0,
                "conversion_rate": 0.0,
                "top_products": [],
                "weekly_revenue": [0] * 4,  # 4 weeks of zero data
                "weekly_sales": [0] * 4,
                "period": "last_30_days"
            }

        # Single query to get all products
        products_cursor = db["products"].find({"_id": {"$in": product_object_ids}})
        products = list(products_cursor)
        
        # Calculate total views
        total_views = sum([product.get("views", 0) for product in products])
        
        # Calculate conversion rate (avoid division by zero)
        conversion_rate = round((total_sales / total_views * 100), 2) if total_views > 0 else 0.0

        # Get top 3 performing products (limited for Emerald tier)
        top_products = sorted(products, key=lambda x: x.get("revenue", 0), reverse=True)[:3]
        top_products_data = [
            {
                "product_id": str(product.get("_id")),
                "title": product.get("title", ""),
                "sales": product.get("sales", 0),
                "revenue": product.get("revenue", 0.0),
                "views": product.get("views", 0)
            }
            for product in top_products
        ]

        # Get weekly revenue/sales data for the last 30 days (4 weeks)
        one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        
        # Create weekly buckets
        weekly_revenue = [0] * 4
        weekly_sales = [0] * 4
        
        # Query transactions for the last 30 days
        transactions_cursor = db["payments"].find({
            "seller_user_id": user_id,
            "created_at": {"$gte": one_month_ago}
        })
        
        transactions = list(transactions_cursor)
        
        # Group transactions by week
        for transaction in transactions:
            created_at = transaction.get("created_at")
            if isinstance(created_at, datetime.datetime):
                days_ago = (datetime.datetime.now() - created_at).days
                week_index = min(days_ago // 7, 3)  # 0-3 weeks (0 = most recent)
                week_index = 3 - week_index  # Reverse so index 0 = oldest week
                
                weekly_revenue[week_index] += transaction.get("price", 0) / 100  # Convert from cents
                weekly_sales[week_index] += 1

        return {
            "total_sales": total_sales,
            "total_revenue": total_rev,
            "total_views": total_views,
            "conversion_rate": conversion_rate,
            "top_products": top_products_data,
            "weekly_revenue": weekly_revenue,  # Array of 4 weeks for graphing
            "weekly_sales": weekly_sales,      # Array of 4 weeks for graphing
            "period": "last_30_days",
            "num_products": num_products
        }

    @staticmethod
    def get_diamond_analytics(user_id: str) -> dict:
        '''Diamond analytics, all of the emerald stats included, plus more '''
        res = {}
        emerald_stats = Analytics.get_emerald_analytics(user_id)
        monthly_revenue = Analytics.get_monthly_revenue(user_id)
        enhanced_conversion_rates = Analytics.get_enhanced_conversion_rates(user_id)
        products_monthly_rev = Analytics.get_products_monthly_revenue_list(user_id)
        customer_analytics = Analytics.get_customer_analytics_stats(user_id)

        res.update(emerald_stats)
        res["monthly_revenue"] = monthly_revenue
        res["converstion_rates"] = enhanced_conversion_rates
        res["products_monthly_rev"] = products_monthly_rev
        res["customer_analytics"] = customer_analytics
        return res

    @staticmethod
    def get_enterprise_analytics(user_id:str) -> dict:
        pass

    @staticmethod
    def get_monthly_revenue(user_id: str) -> List[int]:
        """
        Ultra-fast version using MongoDB's date operators.
        """
        db = MongoDBConnection.get_db()
        now = datetime.datetime.now()
        
        # Single aggregation pipeline that buckets by month automatically
        pipeline = [
            {
                "$match": {
                    "seller_user_id": user_id,
                    "created_at": {
                        "$gte": datetime.datetime(now.year - 1, now.month, 1)
                    }
                }
            },
            {
                "$project": {
                    "price": 1,
                    "monthYear": {
                        "$dateToString": {
                            "format": "%Y-%m",
                            "date": "$created_at"
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": "$monthYear",
                    "revenue": {"$sum": "$price"}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]
        
        result = list(db["payments"].aggregate(pipeline))
        
        # Convert to array format for frontend
        monthly_revenue = [0] * 12
        current_month = now.replace(day=1)
        
        for entry in result:
            month_str = entry["_id"]  # Format: "YYYY-MM"
            revenue = entry["revenue"] // 100  # Convert cents to dollars
            
            # Calculate position in array (0 = oldest, 11 = newest)
            year, month = map(int, month_str.split('-'))
            entry_date = datetime.datetime(year, month, 1)
            
            # Calculate months difference
            months_diff = (current_month.year - entry_date.year) * 12 + (current_month.month - entry_date.month)
            
            if 0 <= months_diff < 12:
                index = 11 - months_diff  # Reverse so newest is at end
                monthly_revenue[index] = revenue
        
        return monthly_revenue


    @staticmethod
    def get_enhanced_conversion_rates(user_id) -> dict:
        db = MongoDBConnection.get_db()
        user = User.get_user_info(user_id)
        store = Store.get_store_info(user.get("store"))

        product_object_ids = [ObjectId(x) for x in store.get("products")]

        pipeline = [
            {
                "$match": {
                    "_id": {"$in": product_object_ids}  # Fixed: removed $ prefix
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_views": {"$sum": "$views"},  
                    "total_favorites": {"$sum": "$favorite_count"},  
                    "total_purchases": {"$sum": "$sales"} 
                } 
            }
        ]

        result_cursor = db["products"].aggregate(pipeline)
        result_list = list(result_cursor)

        result = result_list[0]  # Fixed: get first result from cursor
    
        total_views = result.get("total_views", 0)
        total_favorites = result.get("total_favorites", 0)
        total_purchases = result.get("total_purchases", 0)
        
        view_to_favorite = round((total_favorites / total_views) * 100, 2) if total_views > 0 else 0.0
        favorite_to_purchase = round((total_purchases / total_favorites) * 100, 2) if total_favorites > 0 else 0.0
        view_to_purchase = round((total_purchases / total_views) * 100, 2) if total_views > 0 else 0.0

        return {
            "view_to_favorite": view_to_favorite,
            "favorite_to_purchase": favorite_to_purchase, 
            "view_to_purchase": view_to_purchase,
            "total_favorites": total_favorites,
        }

    @staticmethod
    def get_products_monthly_revenue(user_id: str) -> dict:
        """
        Get monthly revenue for each product in user's store.
        Returns dict with product info including titles and 12-month revenue arrays.
        """
        db = MongoDBConnection.get_db()
        now = datetime.datetime.now()
        user = User.get_user_info(user_id)
        store = Store.get_store_info(user.get("store"))

        if not store.get("products"):
            return {}

        product_object_ids = [ObjectId(x) for x in store.get("products")]
        product_ids_str = store.get("products")  

        # First, get all product info (titles, etc.) in one query
        products_cursor = db["products"].find(
            {"_id": {"$in": product_object_ids}},
            {"title": 1, "_id": 1}  
        )

        products_info = {str(p["_id"]): p["title"] for p in products_cursor}

        # Single optimized aggregation query for ALL products
        pipeline = [
            {
                "$match": {
                    "seller_user_id": user_id,
                    "product_id": {"$in": product_ids_str},  
                    "created_at": {
                        "$gte": datetime.datetime(now.year - 1, now.month, 1)
                    }
                }
            },
            {
                "$project": {
                    "product_id": 1,
                    "price": 1,
                    "monthYear": {
                        "$dateToString": {
                            "format": "%Y-%m",
                            "date": "$created_at"
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "product_id": "$product_id",
                        "month": "$monthYear"
                    },
                    "revenue": {"$sum": "$price"}
                }
            },
            {
                "$sort": {"_id.month": 1}
            }
        ]

        # Execute single aggregation query
        results = list(db["payments"].aggregate(pipeline))

        # Initialize result structure for all products
        products_revenue = {}
        current_month = now.replace(day=1)

        # Initialize each product with empty revenue array and title
        for product_id in product_ids_str:
            products_revenue[product_id] = {
                "product_id": product_id,
                "title": products_info.get(product_id, "Unknown Product"),
                "monthly_revenue": [0] * 12  # 12 months, index 0 = oldest
            }

        # Process aggregation results
        for entry in results:
            product_id = entry["_id"]["product_id"]
            month_str = entry["_id"]["month"]  # Format: "YYYY-MM"
            revenue = entry["revenue"] // 100  # Convert cents to dollars

            # Calculate position in array (0 = oldest, 11 = newest)
            year, month = map(int, month_str.split('-'))
            entry_date = datetime.datetime(year, month, 1)

            # Calculate months difference
            months_diff = (current_month.year - entry_date.year) * 12 + (current_month.month - entry_date.month)

            if 0 <= months_diff < 12 and product_id in products_revenue:
                index = 11 - months_diff  # Reverse so newest is at end
                products_revenue[product_id]["monthly_revenue"][index] = revenue

        return products_revenue

    # Alternative version that returns a list format (might be easier for frontend)
    @staticmethod
    def get_products_monthly_revenue_list(user_id: str) -> List[dict]:
        """
        Same as above but returns a list instead of dict for easier frontend iteration.
        """
        products_dict = Analytics.get_products_monthly_revenue(user_id)
        return list(products_dict.values())

    # Alternative ultra-fast version using advanced aggregation with lookup
    @staticmethod
    def get_customer_analytics_stats(user_id: str) -> dict:
        """
        Even faster version using MongoDB $lookup to join user data in single query.
        """
        db = MongoDBConnection.get_db()
        
        pipeline = [
            {
                "$match": {
                    "seller_user_id": user_id
                }
            },
            {
                "$group": {
                    "_id": "$buyer_user_id",
                    "total_spent": {"$sum": "$price"},
                    "purchase_count": {"$sum": 1},
                    "avg_purchase_value": {"$avg": "$price"}
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "user_info",
                    "pipeline": [
                        {"$project": {"username": 1, "email": 1}}
                    ]
                }
            },
            {
                "$project": {
                    "buyer_user_id": "$_id",
                    "total_spent": {"$divide": ["$total_spent", 100]},
                    "purchase_count": 1,
                    "avg_purchase_value": {"$divide": ["$avg_purchase_value", 100]},
                    "username": {"$arrayElemAt": ["$user_info.username", 0]},
                    "email": {"$arrayElemAt": ["$user_info.email", 0]},
                    "_id": 0
                }
            },
            {
                "$sort": {"total_spent": -1}
            }
        ]
        
        customer_stats = list(db["payments"].aggregate(pipeline))
        
        if not customer_stats:
            return None
        
        # Process results
        one_time_customers = sum(1 for c in customer_stats if c["purchase_count"] == 1)
        returning_customers = sum(1 for c in customer_stats if c["purchase_count"] > 1)
        total_revenue = sum(c["total_spent"] for c in customer_stats)
        total_customers = len(customer_stats)
        
        # Top 5 customers (already sorted by revenue)
        top_customers = [
            {
                "user_id": str(customer["buyer_user_id"]),
                "username": customer.get("username", "Unknown User"),
                "email": customer.get("email", "No email"),
                "total_spent": round(customer["total_spent"], 2),
                "purchase_count": customer["purchase_count"],
            }
            for customer in customer_stats[:5]
        ]
        
        return {
            "one_time_customers": one_time_customers,
            "returning_customers": returning_customers,
            "total_customers": total_customers,
            "average_customer_value": round(total_revenue / total_customers, 2),
            "total_customer_revenue": round(total_revenue, 2),
            "customer_retention_rate": round((returning_customers / total_customers * 100), 2) if total_customers > 0 else 0,
            "top_customers": top_customers
        }