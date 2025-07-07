from backend.services.User import User
from backend.services.Product import Product
from backend.services.Store import Store
from lib.Mongo import MongoDBConnection
from bson import ObjectId
from backend.services.transactions.Invoice import Invoice
import datetime
from typing import List
import stripe
import os
from backend.middleware.product.Product import ProductMiddleware
from backend.middleware.user.User import UserMiddleware
stripe.api_key = os.getenv("STRIPE_TEST_KEY") if os.getenv("NODE_ENV") == "development" else os.getenv("STRIPE_PROD_KEY")

class Payments:
    base_url = "" if os.getenv("NODE_ENV") == "production" else "http://localhost:3000"
    
    @staticmethod
    def exists(payment_id):
        pass

    @staticmethod
    def get(payment_id):
        pass

    # Creates the payment model to add to database and updates information between the buyer
    # and seller of the payment
    @staticmethod
    def create(buyer_user_id, seller_user_id, product_id, price, invoice_id, metadata):

        if not User.exists(seller_user_id) or not User.exists(buyer_user_id):
            raise Exception("Creating payment failed, users do not exist")
        
        # Create payment object and put inside database
        payment_id = Payments.add(buyer_user_id, seller_user_id, product_id, price, metadata, invoice_id)
        
        db = MongoDBConnection.get_db()
        db["users"].update_one(
            {"_id": ObjectId(buyer_user_id)},
            {
                "$push": {
                    "purchased_automations": product_id,
                    "transactions": {"type": "payment", "id": payment_id}
                }
            }
        )

        # Update seller / seller's store (equivalent)
        store_id = User.get_user_info(seller_user_id)
        
        db["stores"].update_one(
            {"_id": ObjectId(store_id)},
            {
                "$inc": {
                    "sales": 1,
                    "total_revenue": price,
                    "balance": price
                }
            }
        )
        
        return {"payment": payment_id, "store": store_id}

    # Adds a payment to the payments collection, given necessary data.
    @staticmethod
    def add(buyer_user_id, seller_user_id, product_id, price, metadata, invoice_id):
        
        new_payment_data = {
            "buyer_user_id": str(buyer_user_id),
            "seller_user_id": str(seller_user_id),
            "product_id": str(product_id),
            "price": price,
            "created_at": datetime.datetime.now(),
            "metadata": metadata,
            "invoice_id": invoice_id
        }

        db = MongoDBConnection.get_db()
        result = db["payments"].insert_one(new_payment_data)
        payment_id = str(result.inserted_id)
        return payment_id

    @staticmethod
    def calculate_marketplace_fees(amount: float, buyer_tier: str = "free") -> dict:
        """Calculate platform fees, processing fees, and seller payout"""
        transaction_fee_percentage = 0.0 if buyer_tier == "enterprise" else 0.02 if buyer_tier == "diamond" else 0.05 if buyer_tier == "emerald" else 0.1
        processing_fee = round(amount * transaction_fee_percentage, 2)
        total_amount = round(amount + processing_fee, 2)
        
        return {
            "seller_payout": amount,
            "buyer_processing_fee": processing_fee,
            "total_amount": total_amount
        }

    @staticmethod
    @ProductMiddleware.validate_product_exists
    @UserMiddleware.validate_user_exists
    @ProductMiddleware.validate_product_ownership
    def create_checkout_session(product_id: str, buyer_id: str, user_id: str, buyer_tier: str):
        if not User.exists(buyer_id):
            raise Exception("buyer id does not exist")
        
        product_price = float(Product.get(product_id).get("price"))
        product_title = str(Product.get(product_id).get("title"))
        marketplace_fees = Payments.calculate_marketplace_fees(product_price, buyer_tier=buyer_tier)
        total_price = marketplace_fees["total_amount"]

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'{product_title}',
                    },
                    'unit_amount': int(total_price * 100),  
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{Payments.base_url}/products/{product_id}/success",
            cancel_url=f"{Payments.base_url}/products/{product_id}/cancel",
            metadata={
                "buyer_id": buyer_id,
                "seller_id": user_id,
                "product_id": product_id,
            }
        )
        
        return checkout_session.url
    
    # Handles when a user successfully buys a product (stripe webhook handler)
    @staticmethod
    def handle_payment_complete(event_data: dict):
        payment_status = event_data["payment_status"]
        if payment_status == "unpaid":
            return # skip if payment is not paid

        # Extract data from checkout session
        amount_total = event_data["amount_total"]
        buyer_id = event_data["metadata"]["buyer_id"]
        seller_id = event_data["metadata"]["seller_id"]
        product_id = event_data["metadata"]["product_id"]
        created_at = datetime.datetime.fromtimestamp(event_data["created"])
        customer = event_data["customer"]
        stripe_invoice_id = event_data["invoice"]
        
        print("Customer Details", event_data["customer_details"])

        # Extract data from invoice from the checkout session
        si = Invoice.get_stripe_invoice(stripe_invoice_id)

        country = si["account_country"]
        invoice_created = si["created"]
        customer_address = si["customer_address"]
        customer_name = si["customer_name"]
        invoice_pdf = si["invoice_pdf"]
        customer_email = si["customer_email"]

        # Extract data from the actual product bought
        product = Product.get(product_id)
        product_price = product.get("price")

        # Create a payment and invoice object
        created_invoice_id = Invoice.create(
            user_id=buyer_id, 
            amount=amount_total, 
            stripe_invoice_id=stripe_invoice_id, 
            type="payment", 
            paid_at=created_at,
            payment_id=None,  # Will be set after payment creation
            subscription_id=None,
            seller_id=seller_id,
            product_id=product_id,
            metadata={
                "customer": customer,
                "customer_address": customer_address,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "invoice_pdf": invoice_pdf,
                "country": country
            }
        )

        created_payment_id = Payments.add(
            buyer_user_id=buyer_id,
            seller_user_id=seller_id,
            product_id=product_id,
            price=product_price,
            metadata=event_data["metadata"],
            invoice_id=created_invoice_id
        )

        # Update the invoice with the payment ID
        Invoice.update(created_invoice_id, {"payment_id": created_payment_id})

        # Update buyer (add to transactions and purchased automations)
        db = MongoDBConnection.get_db()
        
        # Update buyer user
        db["users"].update_one(
            {"_id": ObjectId(buyer_id)},
            {
                "$push": {
                    "purchased_automations": product_id,
                    "transactions": {
                        "type": "payment", 
                        "id": created_payment_id,
                        "amount": product_price,
                        "product_id": product_id,
                        "created_at": created_at
                    }
                }
            }
        )

        # Update seller's store
        seller_info = User.get_user_info(seller_id)
        store_id = seller_info.get("store")
        
        db["stores"].update_one(
            {"_id": ObjectId(store_id)},
            {
                "$inc": {
                    "sales": 1,
                    "total_revenue": product_price,
                    "balance": product_price
                },
                "$push": {
                    "recent_sales": {
                        "payment_id": created_payment_id,
                        "product_id": product_id,
                        "buyer_id": buyer_id,
                        "amount": product_price,
                        "created_at": created_at
                    }
                }
            }
        )

        # Update product statistics
        db["products"].update_one(
            {"_id": ObjectId(product_id)},
            {
                "$inc": {
                    "purchase_count": 1,
                    "total_revenue": product_price
                },
            }
        )

        return


    @staticmethod
    def get_payment_status(payment_id: str) -> dict:
        """Get detailed payment status and history"""
        pass

    @staticmethod
    def schedule_seller_payout(seller_id: str, amount: float, payout_date: datetime = None) -> str:
        """Schedule payout to seller"""
        pass

    @staticmethod
    def get_seller_earnings(seller_id: str, time_period: str = "30d") -> dict:
        """Get seller earnings summary"""
        pass

    @staticmethod
    def get_payment_analytics(time_period: str = "30d") -> dict:
        """Get payment analytics (volume, fees, success rate)"""
        pass

    @staticmethod
    def get_high_value_payments(threshold: float = 1000.0, time_period: str = "30d") -> List[dict]:
        """Get high-value payments for monitoring"""
        pass

