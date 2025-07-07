from typing import List, Dict
import pymongo
from backend.lib.Mongo import MongoDBConnection
import datetime
from pymongo import TEXT

class Searcher:

    @staticmethod
    def get_top_products(limit: int = 50) -> List[Dict]:
        """
        Retrieve the top products based on their score.
        """
        db = MongoDBConnection.get_db()
        result = db["products"].find().sort("score", pymongo.DESCENDING).limit(limit)
        
        return list(result)
    
    @staticmethod
    def get_top_product_by_category(limit: int = 50, category: str = "") -> List[Dict]:
        
        db = MongoDBConnection.get_db()
        result = db["products"].find({"tags": {"$in": [category]}}).sort("score", pymongo.DESCENDING).limit(limit)

        return list(result)
    
    @staticmethod
    def get_top_stores(limit: int = 20) -> List[Dict]:
        db = MongoDBConnection.get_db()
        top_stores = db["stores"].find().sort("score", pymongo.DESCENDING).limit(limit)

        return list(top_stores)

    @staticmethod
    def get_top_stores_by_category(limit: int = 20, category: str = "") -> List[Dict]:
        
        db = MongoDBConnection.get_db()
        result = db["stores"].find({"tags": {"$in": [category]}}).sort("score", pymongo.DESCENDING).limit(limit)

        return list(result)

    @staticmethod
    def get_trending_products(limit: int = 50) -> List[Dict]:
        """Get products with highest score increase in time window"""
        db = MongoDBConnection.get_db()
        one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)

        result = db["products"].aggregate(
            {"$match": {"$gte": one_month_ago}},
            {"$sort": {"views": -1}},
            {"$limit": limit}
        )

        return list(result)
    
    @staticmethod
    def get_new_products(limit: int = 50) -> List[Dict]:
        '''Gets the the products made within the past week, sorted by score'''
        db = MongoDBConnection.get_db()
        one_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)

        result = db["products"].aggregate(
            {"$match" : {"$gte": one_week_ago}},
            {"$sort": {"score": -1}},
            {"$limit": limit}
        )

        return list(result)
    

    @staticmethod
    async def get_products_search(name: str, batch: int):
        ''' Returns products where the title has arg 'name' in it'''
        db = MongoDBConnection.get_db()
        
        # Create case-insensitive regex pattern for substring matching
        search_pattern = {"$regex": name, "$options": "i"}
        
        # Use $facet to search in parallel across different fields and maintain order
        pipeline = [
            {
                "$facet": {
                    # First priority: title matches
                    "title_matches": [
                        {"$match": {"title": search_pattern}},
                        {"$addFields": {"search_priority": 1}}
                    ],
                    # Second priority: description matches
                    "description_matches": [
                        {"$match": {
                            "description": search_pattern,
                            "title": {"$not": search_pattern}  # Exclude already found in title
                        }},
                        {"$addFields": {"search_priority": 2}}
                    ],
                    # Third priority: tags matches
                    "tags_matches": [
                        {"$match": {
                            "tags": {"$elemMatch": search_pattern},
                            "title": {"$not": search_pattern},
                            "description": {"$not": search_pattern}
                        }},
                        {"$addFields": {"search_priority": 3}}
                    ],
                    # Fourth priority: features matches (searching in feature names/descriptions)
                    "features_matches": [
                        {"$match": {
                            "$or": [
                                {"features.name": search_pattern},
                                {"features.description": search_pattern}
                            ],
                            "title": {"$not": search_pattern},
                            "description": {"$not": search_pattern},
                            "tags": {"$not": {"$elemMatch": search_pattern}}
                        }},
                        {"$addFields": {"search_priority": 4}}
                    ],
                    # Fifth priority: about matches
                    "about_matches": [
                        {"$match": {
                            "about": {"$elemMatch": search_pattern},
                            "title": {"$not": search_pattern},
                            "description": {"$not": search_pattern},
                            "tags": {"$not": {"$elemMatch": search_pattern}},
                            "$nor": [
                                {"features.name": search_pattern},
                                {"features.description": search_pattern}
                            ]
                        }},
                        {"$addFields": {"search_priority": 5}}
                    ],
                    # Sixth priority: use_cases matches
                    "use_cases_matches": [
                        {"$match": {
                            "$or": [
                                {"use_cases.title": search_pattern},
                                {"use_cases.description": search_pattern}
                            ],
                            "title": {"$not": search_pattern},
                            "description": {"$not": search_pattern},
                            "tags": {"$not": {"$elemMatch": search_pattern}},
                            "about": {"$not": {"$elemMatch": search_pattern}},
                            "$nor": [
                                {"features.name": search_pattern},
                                {"features.description": search_pattern}
                            ]
                        }},
                        {"$addFields": {"search_priority": 6}}
                    ]
                }
            },
            {
                # Combine all results maintaining priority order
                "$project": {
                    "all_matches": {
                        "$concatArrays": [
                            "$title_matches",
                            "$description_matches", 
                            "$tags_matches",
                            "$features_matches",
                            "$about_matches",
                            "$use_cases_matches"
                        ]
                    }
                }
            },
            {
                "$unwind": "$all_matches"
            },
            {
                "$replaceRoot": {"newRoot": "$all_matches"}
            },
            {
                # Sort by priority first, then by score for ties
                "$sort": {"search_priority": 1, "score": -1}
            }
        ]

        res = db["products"].aggregate(pipeline)
        return list(res[batch * 50:batch * 50 + 50])