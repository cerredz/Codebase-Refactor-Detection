from typing import Dict, List, Any, Tuple
from backend.services.Product import Product
from backend.services.Workflow import Workflow
from backend.services.Store import Store
from backend.lib.Mongo import MongoDBConnection
from backend.services.transactions.Subscriptions import Subscription
from bson import ObjectId

import pymongo


class Ranker:
    
    # ===== CORE SCORING METHODS =====
    @staticmethod
    def calculate_content_completeness_score(product_id: str) -> float:
        """Calculate score based on description quality, features, documentation"""
        content_score = 0
        product = Product.get(product_id)
        about = product.get("about", None)
        total_about_size = 0

        # grade the about string of a product
        if not about: 
            content_score -= 50

        if len(about) > 5:
            content_score += 10

        for str in about:
            total_about_size += len(str)
        
        if total_about_size < 100:
            content_score -= 10

        if total_about_size > 100 and total_about_size < 300:
            content_score += 25
        
        if total_about_size > 300:
            content_score += 50

        # grade the features
        features = product.get("features", None)
        if not features:
            content_score -= 50
        
        if len(features) < 3: 
            content_score += 10
        elif len(features) > 3 and len(features) < 12:
            content_score += 25
        elif len(features) > 12 and len(features) < 25:
            content_score += 15
        elif len(features) > 25:
            content_score += 5

        # grade the tags
        tags = product.get("tags", None)

        if not tags: 
            content_score -= 50
        
        if len(tags) < 3:
            content_score += 15
        elif len(tags) > 3 and len(tags) < 8:
            content_score += 25
        elif len(tags) > 8:
            content_score += 5

        # grade the use_cases
        use_cases = product.get("use_cases", None)
        if not use_cases: 
            content_score -= 25
        
        content_score += min(50, 7 * len(use_cases))

        # grade the faqs
        faqs = product.get("faqs", None)
        content_score += min(35, 5 * len(faqs))

        return round(content_score, 2)
    
    @staticmethod
    def calculate_media_richness_score(product_id: str) -> float:
        """Calculate score based on images, videos, demos"""
        product = Product.get(product_id)
        thumbnail = product.get("thumbnail", None)
        pictures = product.get("pictures", None)
        instructions = product.get("instructions", None)
        instructions_link = product.get("instruction_links", None)

        media_score = 0

        if not thumbnail:
            media_score -= 50
        
        if not pictures:
            media_score -= 50

        if not instructions:
            media_score -= 50

        media_score += (25 * len(pictures))

        if instructions_link:
            media_score += 25
        
        media_score += min(50, 10 * len(instructions))

        return round(media_score, 2)
    
    @staticmethod
    def calculate_technical_quality_score(product_id: str) -> float:
        """Calculate score based on workflow complexity, integrations, performance"""
        product = Product.get(product_id)
        workflow_id = product.get("workflow_id")
        workflow = Workflow.get(workflow_id)

        technical_score = 0
        nodes = workflow.get("node_count")
        connections = workflow.get("connections_count")

        technical_score += min(125, 5 * len(nodes))
        technical_score += min(75, 5 * len(connections))

        return round(technical_score, 2)

    @staticmethod
    def calculate_social_proof_score(product_id: str) -> float:
        """Calculate score based on ratings, reviews, downloads, engagement"""
        product = Product.get(product_id)
        views = product.get("views")
        sales = product.get("sales")
        revenue = product.get("revenue")
        price = product.get("price")
        favorite_count = product.get("favorite_count")
        reviews = product.get("reviews")
        review_count = product.get("review_count")
        avg_review = round(sum(reviews) / review_count)

        social_proof_score = 0

        if price != 0 and sales != 0:
            social_proof_score += min(100, int((views / sales) * price))

        social_proof_score += min(25, int(revenue // 1000))
        social_proof_score += (avg_review * 5)
        
        if favorite_count != 0:
            social_proof_score += min(100, (views / favorite_count) * 10)

        return round(social_proof_score, 2)
    
    @staticmethod
    def calculate_seller_reputation_score(user_id: str) -> float:
        """Calculate seller's overall reputation score"""
        pass
    
    @staticmethod
    def calculate_freshness_score(product_id: str) -> float:
        """Calculate score based on last update, maintenance, version history"""
        pass
    
    @staticmethod
    def calculate_overall_quality_score(product_id: str) -> float:
        content_weight = media_weight = .3
        social_weight = .2
        technical_weight = .2

        content_score = content_weight * Ranker.calculate_content_completeness_score(product_id)
        media_score = media_weight * Ranker.calculate_media_richness_score(product_id)
        social_score = social_weight * Ranker.calculate_social_proof_score(product_id)
        technical_score = technical_weight * Ranker.calculate_technical_quality_score(product_id)

        db = MongoDBConnection.get_db()
        user_id = Product.get(product_id).get("user_id")
        subscription_id = db["subscriptions"].find_one({"user_id": user_id, "active": True})
        overall_score = int(content_score + media_score + social_score + technical_score)

        if subscription_id and subscription_id.get("verified") == True:
            return overall_score + 100

        return overall_score
    
    # ===== BATCH PROCESSING METHODS =====
    @staticmethod
    def recalculate_all_product_scores() -> Dict[str, int]:
        """Batch recalculate scores for all products (background job)"""
        pass
    
    @staticmethod
    def recalculate_scores_for_products(product_ids: List[str]):
        """Batch recalculate scores for specific products"""
        if not product_ids:
            return {}
        
        db = MongoDBConnection.get_db()
        results = {}
        
        # Prepare bulk operations for efficiency
        bulk_operations = []
        
        for product_id in product_ids:
            try:
                # Calculate score for individual product
                score = Ranker.calculate_overall_quality_score(product_id)
                results[product_id] = score
                
                # Add to bulk operations
                bulk_operations.append({
                    "updateOne": {
                        "filter": {"_id": ObjectId(product_id)},
                        "update": {"$set": {"score": score}}
                    }
                })
                
            except Exception as e:
                print(f"Error calculating score for product {product_id}: {e}")
                results[product_id] = None
        
        # Execute bulk update if we have operations
        if bulk_operations:
            try:
                result = db["products"].bulk_write([
                    pymongo.UpdateOne(
                        filter=op["updateOne"]["filter"],
                        update=op["updateOne"]["update"]
                    ) for op in bulk_operations
                ])
                print(f"Updated {result.modified_count} products with new scores")
            except Exception as e:
                print(f"Error executing bulk update: {e}")
        
        return results
    
    @staticmethod
    def recalculate_seller_reputation_scores() -> Dict[str, float]:
        """Batch recalculate all seller reputation scores"""
        pass
    
    
    # ===== STORE RANKING METHODS =====
    @staticmethod
    def calculate_store_quality_score(store_id: str) -> float:
        """Calculate overall store quality based on products and seller metrics"""
        db = MongoDBConnection.get_db()
        store = Store.get_store_info(store_id)
        product_ids = [ObjectId(pid) for pid in store.get("products", [])]
        
        # Single aggregation query to get average score
        result = db["products"].aggregate([
            {"$match": {"_id": {"$in": product_ids}}},
            {"$group": {"_id": None, "avg_score": {"$avg": "$score"}}}
        ])
        
        return next(result, {}).get("avg_score", 0) or 0
    
    
    
    @staticmethod
    def get_store_ranking_position(store_id: str) -> int:
        """Get store's position in overall store rankings"""
        pass
    
    
    # ===== ANALYTICS & MONITORING METHODS =====
    @staticmethod
    def get_score_distribution() -> Dict[str, int]:
        """Get distribution of scores across all products"""
        pass
    
    
    @staticmethod
    def detect_trending_categories() -> List[Dict]:
        """Detect which categories are trending upward"""
        pass
    
    @staticmethod
    def analyze_score_correlation(metric1: str, metric2: str) -> float:
        """Analyze correlation between different scoring metrics"""
        pass
    
    # ===== UPDATE & MAINTENANCE METHODS =====
    @staticmethod
    def update_product_engagement_metrics(product_id: str, metrics: Dict) -> bool:
        """Update real-time engagement metrics (views, bookmarks, etc.)"""
        pass
    
    @staticmethod
    def trigger_score_update_on_review(product_id: str, review_data: Dict) -> float:
        """Update scores when new review is added"""
        pass
    
    @staticmethod
    def trigger_score_update_on_purchase(product_id: str) -> float:
        """Update scores when product is purchased"""
        pass
    
    
    # ===== ADMINISTRATIVE METHODS =====
    @staticmethod
    def get_product_score_breakdown(product_id: str) -> Dict[str, float]:
        """Get detailed breakdown of how product score was calculated"""
        pass

    # ===== ADVANCED RANKING FUNCTIONS =====
    @staticmethod
    def get_ranking_distribution() -> dict:
        """Get distribution of ranking scores across all products"""
        pass

    @staticmethod
    def identify_ranking_outliers(threshold: float = 2.0) -> List[dict]:
        """Identify products with unusual ranking scores"""
        pass

    @staticmethod
    def calculate_category_rankings(category: str, limit: int = 50) -> List[dict]:
        """Calculate rankings within specific category"""
        pass

