import os
import stripe
from backend.services.User import User
from backend.models.Transactions import SubscriptionModel
from backend.middleware.user.User import UserMiddleware
from backend.lib.Mongo import MongoDBConnection
from bson import ObjectId
import datetime
from typing import List
from backend.services.transactions.Invoice import Invoice


class Subscription: 

    # Global subscription objects in stripe
    emerald = ""
    diamond = ""
    enterprise = ""
    base_url = "https://api.stripe.com"

    # Product ID's of Stripe Products (Will be used when creating payment links)
    payment_link_product_ids = {
        "single_resume_purchase": {"test": "", "production": ""},
        "subscriptions": [
            {
                # entry plan pricing ids
                "test": "",
                "production": "",
            },
            {
                # premium plan pricing ids  
                "test": "",
                "production": "",
            },
            {
                # ultimate plan pricing ids
                "test": "",
                "production": "",
            },
        ],
    }

    @staticmethod
    @UserMiddleware.validate_user_exists
    def create_subscription_link(user_id: str, index: int):
        if not User.exists(user_id=user_id):
            raise Exception("Error creating stripe link, user does not exist")

        # Map index to tier
        tier_mapping = {
            0: "emerald",
            1: "diamond", 
            2: "enterprise"  # Changed from "custom" to "enterprise" to match your tier configs
        }
        
        tier = tier_mapping.get(index, "emerald")  # Default to emerald if invalid index

        # Initialize Stripe client based on environment
        stripe_mode = os.getenv('STRIPE_MODE', 'test')

        if stripe_mode != "test":
            stripe_client = stripe
            stripe_client.api_key = os.getenv('STRIPE_SECRET_PRODUCTION_KEY')
        else:
            stripe_client = stripe
            stripe_client.api_key = os.getenv('STRIPE_SECRET_TEST_KEY')

        try:
            # Get appropriate subscription product ID based on index and environment
            subscription_product_id = (
                Subscription.payment_link_product_ids["subscriptions"][index]["production"]
                if stripe_mode != "test"
                else Subscription.payment_link_product_ids["subscriptions"][index]["test"]
            )

            # Determine base redirect URL
            node_env = os.getenv('NODE_ENV', 'development')
            base_redirect_url = "" if node_env == "production" else "http://localhost:3000"

            # Create payment link
            payment_link = stripe_client.PaymentLink.create(
                line_items=[{"price": subscription_product_id, "quantity": 1}],
                metadata={
                    "user_id": user_id,
                    "tier": tier,
                    "subscription_index": str(index)
                },
                after_completion={
                    "type": "redirect",
                    "redirect": {
                        "url": f"{base_redirect_url}/subscription/success",
                    },
                },
            )

            return payment_link.url

        except Exception as error:
            print(f"🔴 Failed To Create Stripe Payment link for {user_id}")
            return {
                "error": True,
                "title": "Internal Server Error",
                "subtitle": "Internal Server Error, Please Try Again Later",
            }

    # TODO: implement below functions
    @staticmethod 
    def create_enterprise_subscription_link():
        pass    


    @staticmethod
    def add_subscription(user_id, tier: str, stripe_subscription_id: str, start: datetime, end: datetime, invoice_id: str, stripe_customer_id: str):
        if not User.exists(user_id=user_id):
            raise Exception("Error adding subscription, user does not exist")
        
        # Define tier configurations
        tier_configs = {
            "emerald": {
                "storage": 1 * 1024 * 1024 * 1024,  # 1GB in bytes
                "products": 10
            },
            "diamond": {
                "storage": 10 * 1024 * 1024 * 1024,  # 10GB in bytes
                "products": 50
            },
            "enterprise": {
                "storage": "unlimited",  # 1TB in bytes
                "products": "unlimited"
            }
        }
        
        # Get tier configuration
        config = tier_configs.get(tier, tier_configs["entry"])
        
        # Get user info to extract stripe customer ID
        user_info = User.get_user_info(user_id)
    
        # Create subscription document
        db = MongoDBConnection.get_db()
        subscription_data = {
            "user_id": user_id,
            "price": 0,  # Will be updated based on actual stripe pricing
            "stripe_customer_id": stripe_customer_id,
            "tier": tier,
            "storage": config["storage"],
            "storage_used": 0.0,
            "products": config["products"],
            "products_used": 0,
            "stripe_subscription_id": stripe_subscription_id,
            "active": True,
            "created_at": datetime.datetime.now(),
            "current_period_start": start,
            "current_period_end": end,
            "verified": tier == "enterprise",  # Enterprise customers are verified by default
            "invoice_id": invoice_id
        }
        
        # Insert subscription into database
        result = db["subscriptions"].insert_one(subscription_data)
        subscription_id = str(result.inserted_id)
        
        # Update user with subscription ID and stripe subscription I
        db["users"].update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "customer": stripe_customer_id,
                    "subscription": subscription_id
                },
                "$push": {
                    "transactions": {"type": "payment", "id": subscription_id}
                }
            }
        )
        
        return subscription_id

    @staticmethod
    def get(subscription_id) -> dict:
        if not Subscription.exists(subscription_id=subscription_id):
            return None
        
        db = MongoDBConnection.get_db()
        subscription = db["subscriptions"].find_one({"_id": ObjectId(subscription_id)})

        sub_model = SubscriptionModel(**subscription)
        return {**sub_model.model_dump()}
    
    @staticmethod
    def exists(subscription_id) -> bool:
        if not subscription_id:
            return False
        
        db = MongoDBConnection.get_db()
        subscription = db["subscriptions"].find_one({"_id": ObjectId(subscription_id)})

        if not subscription or len(subscription) == 0:
            return False
        
        return True

    # Function to either update a user's subscription level or delete it
    @staticmethod
    def update_subscription(event, user_id, old_id, new_tier, invoice_id):
        if not User.exists(user_id=user_id):
            raise Exception("Error adding subscription, user does not exist")

        user = User.get_user_info(user_id)
        old_sub = Subscription.get(old_id)
        
        if not old_sub:
            raise Exception("Old subscription not found")
        
        db = MongoDBConnection.get_db()
        
        # Set old subscription to inactive
        db["subscriptions"].update_one(
            {"_id": ObjectId(old_id)},
            {"$set": {"active": False}}
        )
        
        # If new_tier is 'deleted', just deactivate and don't create new subscription
        if new_tier == 'deleted':
            return None
        
        # Define tier configurations
        tier_configs = {
            "entry": {
                "storage": 1 * 1024 * 1024 * 1024,  # 1GB in bytes
                "products": 5
            },
            "premium": {
                "storage": 10 * 1024 * 1024 * 1024,  # 10GB in bytes
                "products": 25
            },
            "ultimate": {
                "storage": 100 * 1024 * 1024 * 1024,  # 100GB in bytes
                "products": 500
            },
            "enterprise": {
                "storage": "unlimited",  # 1TB in bytes
                "products": "unlimited"
            }
        }
        
        # Get new tier configuration
        config = tier_configs.get(new_tier, tier_configs["entry"])
        
        # Extract stripe subscription ID from event if available
        stripe_subscription_id = getattr(event, 'subscription', None) or old_sub.get("stripe_subscription_id", "")
        
        # Create new subscription with copied storage/product usage stats
        new_subscription_data = {
            "user_id": user_id,
            "price": old_sub.get("price", 0),
            "stripe_customer_id": old_sub.get("stripe_customer_id", ""),
            "tier": new_tier,
            "storage": config["storage"],
            "storage_used": min(old_sub.get("storage_used", 0.0), config["storage"]),  # Don't exceed new limit
            "products": config["products"],
            "products_used": min(old_sub.get("products_used", 0), config["products"]),  # Don't exceed new limit
            "stripe_subscription_id": stripe_subscription_id,
            "active": True,
            "created_at": datetime.datetime.now(),
            "current_period_start": old_sub.get("current_period_start", datetime.datetime.now()),
            "current_period_end": old_sub.get("current_period_end", datetime.datetime.now()),
            "verified": new_tier == "enterprise" or old_sub.get("verified", False),
            "invoice_id": invoice_id
        }
        
        # Insert new subscription
        result = db["subscriptions"].insert_one(new_subscription_data)
        new_subscription_id = str(result.inserted_id)
        
        # Update user with new subscription ID and stripe subscription ID
        User.update_user_info(user_id, {
            "subscription": new_subscription_id
        })
        
        return new_subscription_id

    @staticmethod
    def handle_subscription_complete(event_data: dict):
        """Handle completed subscription checkout session"""
        try:
            payment_status = event_data.get("payment_status")
            if payment_status == "unpaid":
                return  # Skip if payment is not paid

            # Extract data from checkout session
            amount_total = event_data.get("amount_total", 0)
            user_id = event_data.get("metadata", {}).get("user_id")
            tier = event_data.get("metadata", {}).get("tier", "emerald")
            subscription_index = event_data.get("metadata", {}).get("subscription_index", "0")
            created_at = datetime.datetime.fromtimestamp(event_data.get("created", 0))
            customer_id = event_data.get("customer")
            stripe_invoice_id = event_data.get("invoice")
            session_id = event_data.get("id")

            if not user_id:
                raise Exception("No user_id found in checkout session metadata")

            print(f"Processing subscription for user: {user_id}, tier: {tier}")

            # Create subscription in Stripe (this might already exist for subscription mode)
            stripe_subscription_id = event_data.get("subscription")
            
            # Create invoice record
            created_invoice_id = Invoice.create(
                user_id=user_id,
                amount=amount_total,
                stripe_invoice_id=stripe_invoice_id or f"sub_{session_id}",
                type="subscription",
                paid_at=created_at,
                payment_id=None,
                subscription_id=None,  # Will be set after subscription creation
                seller_id=None,  # No seller for subscriptions
                product_id=None,  # No product for subscriptions
                metadata={
                    "tier": tier,
                    "customer_id": customer_id,
                    "stripe_subscription_id": stripe_subscription_id,
                }
            )

            # Create subscription record
            subscription_id = Subscription.add_subscription(
                user_id=user_id,
                tier=tier,
                stripe_subscription_id=stripe_subscription_id,
                start=created_at,
                end=created_at + datetime.timedelta(days=30),  # Default to 30 days, update with actual period
                invoice_id=created_invoice_id,
                stripe_customer_id=customer_id
            )

            # Update invoice with subscription ID
            Invoice.update(created_invoice_id, {"subscription_id": subscription_id})

            # Update user with additional transaction info and customer ID
            db = MongoDBConnection.get_db()
            
            # Add subscription transaction to user
            db["users"].update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$push": {
                        "transactions": {
                            "type": "subscription",
                            "id": subscription_id,
                            "amount": amount_total / 100,  # Convert from cents
                            "tier": tier,
                            "created_at": created_at,
                            "stripe_subscription_id": stripe_subscription_id
                        }
                    },
                    "$set": {
                        "customer": customer_id  # Update customer ID if not already set
                    }
                }
            )

            return

        except Exception as e:
            print(f"❌ Error processing subscription: {e}")
            raise Exception(f"Error handling subscription completion: {e}")

    @staticmethod
    def upgrade_subscription(user_id: str, new_tier: str, prorate: bool = True) -> dict:
        """Upgrade user subscription to higher tier"""
        pass

    @staticmethod
    def downgrade_subscription(user_id: str, new_tier: str, effective_date: datetime = None) -> dict:
        """Downgrade user subscription to lower tier"""
        pass

    @staticmethod
    def cancel_subscription(user_id: str, cancellation_reason: str, immediate: bool = False) -> bool:
        """Cancel user subscription"""
        pass

    @staticmethod
    def reactivate_subscription(user_id: str, reactivation_reason: str) -> bool:
        """Reactivate cancelled subscription"""
        pass

    @staticmethod
    def get_subscription_analytics(time_period: str = "30d") -> dict:
        """Get subscription analytics (churn, revenue, tier distribution)"""
        pass

    @staticmethod
    def calculate_subscription_revenue(time_period: str = "30d") -> dict:
        """Calculate subscription revenue by tier and period"""
        pass

    @staticmethod
    def get_subscription_usage_limits(user_id: str) -> dict:
        """Get current usage against subscription limits"""
        pass

    @staticmethod
    def check_usage_overage(user_id: str) -> dict:
        """Check if user has exceeded subscription limits"""
        pass

    @staticmethod
    def apply_subscription_discount(user_id: str, discount_code: str, duration_months: int = None) -> bool:
        """Apply discount to subscription"""
        pass

    @staticmethod
    def get_expiring_subscriptions(days_ahead: int = 7) -> List[dict]:
        """Get subscriptions expiring soon"""
        pass

    @staticmethod
    def send_renewal_reminder(user_id: str, reminder_type: str) -> bool:
        """Send subscription renewal reminder"""
        pass

    @staticmethod
    def process_failed_payment(subscription_id: str, failure_reason: str) -> dict:
        """Handle failed subscription payment"""
        pass

    @staticmethod
    def update_billing_info(user_id: str, billing_data: dict) -> bool:
        """Update subscription billing information"""
        pass

    @staticmethod
    def get_subscription_history(user_id: str) -> List[dict]:
        """Get complete subscription history for user"""
        pass

    @staticmethod
    def calculate_churn_metrics(time_period: str = "30d") -> dict:
        """Calculate subscription churn metrics"""
        pass

    @staticmethod
    def get_tier_migration_stats() -> dict:
        """Get statistics on tier upgrades/downgrades"""
        pass

    @staticmethod
    def pause_subscription(user_id: str, pause_duration_days: int, reason: str) -> bool:
        """Temporarily pause subscription"""
        pass

    @staticmethod
    def resume_subscription(user_id: str) -> bool:
        """Resume paused subscription"""
        pass

    @staticmethod
    def get_subscription_recommendations(user_id: str) -> dict:
        """Get subscription tier recommendations based on usage"""
        pass

    @staticmethod
    def validate_subscription_limits(user_id: str, action_type: str, resource_size: int = None) -> bool:
        """Validate if user can perform action within subscription limits"""
        pass

    @staticmethod
    async def handle_subscription_updated(event_data: dict):
        """Handle customer.subscription.updated webhook event"""
        try:
            stripe_subscription_id = event_data.get("id")
            if not stripe_subscription_id:
                raise Exception("No subscription ID found in event data")

            # Find existing subscription in our database
            db = MongoDBConnection.get_db()
            existing_subscription = db["subscriptions"].find_one({
                "stripe_subscription_id": stripe_subscription_id
            })

            if not existing_subscription:
                print(f"⚠️ Subscription not found in database: {stripe_subscription_id}")
                return  # Skip if subscription doesn't exist in our system

            user_id = existing_subscription["user_id"]
            old_tier = existing_subscription["tier"]
            
            # Extract new subscription data
            status = event_data.get("status", "active")
            current_period_start = datetime.datetime.fromtimestamp(event_data.get("current_period_start", 0))
            current_period_end = datetime.datetime.fromtimestamp(event_data.get("current_period_end", 0))
            cancel_at_period_end = event_data.get("cancel_at_period_end", False)
            canceled_at = event_data.get("canceled_at")
            canceled_at_datetime = datetime.datetime.fromtimestamp(canceled_at) if canceled_at else None
            
            # Extract pricing information and tier from metadata
            items = event_data.get("items", {}).get("data", [])
            if not items:   
                print("⚠️ No subscription items found")
                return

            price_id = items[0].get("price", {}).get("id", "")
            unit_amount = items[0].get("price", {}).get("unit_amount", 0)  # Amount in cents
            
            # Determine new tier from subscription metadata
            metadata = event_data.get("metadata", {})
            new_tier = metadata.get("tier", "emerald")  # Default to emerald if no tier specified
            
            print(f"Processing subscription update for user: {user_id}")
            print(f"Status: {status}, Old tier: {old_tier}, New tier: {new_tier}")
            print(f"Period: {current_period_start} to {current_period_end}")
            
            # Update subscription record
            update_data = {
                "current_period_start": current_period_start,
                "current_period_end": current_period_end,
                "price": unit_amount,
                "active": status == "active",
                "cancel_at_period_end": cancel_at_period_end
            }
            
            if canceled_at_datetime:
                update_data["canceled_at"] = canceled_at_datetime

            # Handle tier changes
            if new_tier != old_tier:
                print(f"🔄 Tier change detected: {old_tier} → {new_tier}")
                
                # Get new tier configuration
                tier_configs = {
                    "emerald": {
                        "storage": 1 * 1024 * 1024 * 1024,  # 1GB in bytes
                        "products": 10
                    },
                    "diamond": {
                        "storage": 10 * 1024 * 1024 * 1024,  # 10GB in bytes
                        "products": 50
                    },
                    "enterprise": {
                        "storage": "unlimited",
                        "products": "unlimited"
                    }
                }
                
                new_config = tier_configs.get(new_tier, tier_configs["emerald"])
                
                # Update tier and limits, but preserve usage
                update_data.update({
                    "tier": new_tier,
                    "storage": new_config["storage"],
                    "products": new_config["products"],
                    "verified": new_tier == "enterprise" or existing_subscription.get("verified", False)
                })
                
                # If downgrading, ensure usage doesn't exceed new limits
                if new_config["storage"] != "unlimited":
                    current_storage_used = existing_subscription.get("storage_used", 0)
                    if current_storage_used > new_config["storage"]:
                        update_data["storage_used"] = new_config["storage"]
                
                if new_config["products"] != "unlimited":
                    current_products_used = existing_subscription.get("products_used", 0)
                    if current_products_used > new_config["products"]:
                        update_data["products_used"] = new_config["products"]

            # Handle subscription cancellation
            if status in ["canceled", "unpaid"] or cancel_at_period_end:
                update_data["active"] = False
                print(f"🚫 Subscription marked as inactive: {status}")

            # Update subscription in database
            result = db["subscriptions"].update_one(
                {"stripe_subscription_id": stripe_subscription_id},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                print(f"✅ Subscription updated successfully")
                
                # Add transaction record for significant changes
                if new_tier != old_tier or status == "canceled":
                    transaction_type = "subscription"
                    
                    db["users"].update_one(
                        {"_id": ObjectId(user_id)},
                        {
                            "$push": {
                                "transactions": {
                                    "type": transaction_type,
                                    "id": str(existing_subscription["_id"]),
                                    "tier": new_tier,
                                    "amount": unit_amount / 100,  # Convert from cents
                                    "status": status,
                                    "created_at": datetime.datetime.now(),
                                    "stripe_subscription_id": stripe_subscription_id
                                }
                            }
                        }
                    )

                # Create invoice for billing period changes (renewals)
                latest_invoice = event_data.get("latest_invoice")
                if latest_invoice and unit_amount > 0:
                    # Check if we already have this invoice
                    existing_invoice = db["invoices"].find_one({
                        "stripe_invoice_id": latest_invoice
                    })
                    
                    if not existing_invoice:
                        # Create new invoice for this billing period
                        Invoice.create(
                            user_id=user_id,
                            amount=unit_amount,
                            stripe_invoice_id=latest_invoice,
                            type="subscription",
                            paid_at=current_period_start,
                            payment_id=None,
                            subscription_id=str(existing_subscription["_id"]),
                            seller_id=None,
                            product_id=None,
                            metadata={
                                "tier": new_tier,
                                "billing_period_start": current_period_start.isoformat(),
                                "billing_period_end": current_period_end.isoformat(),
                                "subscription_status": status
                            }
                        )
                        print(f"📄 Created invoice for billing period: {latest_invoice}")

            return

        except Exception as e:
            print(f"❌ Error processing subscription update: {e}")
            raise Exception(f"Error handling subscription update: {e}")

    @staticmethod
    def _determine_tier_from_price_id(price_id: str) -> str:
        """Determine subscription tier based on Stripe price ID"""
        # Get environment and price mappings
        stripe_mode = os.getenv('STRIPE_MODE', 'test')
        price_mappings = Subscription.payment_link_product_ids["subscriptions"]
        
        # Check each tier's price ID
        for index, tier_prices in enumerate(price_mappings):
            tier_price_id = tier_prices["production"] if stripe_mode != "test" else tier_prices["test"]
            if price_id == tier_price_id:
                tier_mapping = {0: "emerald", 1: "diamond", 2: "enterprise"}
                return tier_mapping.get(index, "emerald")
        
        # Fallback: try to determine by price amount if price ID not found
        # This would require fetching the price from Stripe API
        print(f"⚠️ Unknown price ID: {price_id}, defaulting to emerald tier")
        return "emerald"




    



