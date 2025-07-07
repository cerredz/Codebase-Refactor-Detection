import requests
import os
import stripe
from backend.services.User import User
from backend.services.Store import Store
from lib.Mongo import MongoDBConnection
from bson import ObjectId
import datetime
from typing import List

# Set up Stripe API key
stripe.api_key = os.getenv("STRIPE_TEST_KEY") if os.getenv("NODE_ENV") == "development" else os.getenv("STRIPE_PROD_KEY")

class Invoice:
    '''
    Creates an invoice and inputs it into the database
    '''
    @staticmethod
    def create(user_id: str, amount: int, stripe_invoice_id: str, type: str, paid_at: datetime, metadata=None, payment_id=None, subscription_id=None, seller_id=None, product_id=None):
        if not User.exists(user_id) or seller_id and not User.exists(seller_id):
            raise Exception("Error creating invoice, user id's passed in do not exist")
        
        new_invoice_data = {
            "payment_id": payment_id if payment_id else "",
            "subscription_id": subscription_id if subscription_id else "",
            "user_id": user_id,
            "seller_id": seller_id if seller_id else "",
            "product_id": product_id if product_id else "",
            "amount": amount,
            "currency": "usd",
            "stripe_invoice_id": stripe_invoice_id, 
            "created_at": datetime.datetime.now(),
            "paid_at": paid_at,
            "invoice_type": type,
            "metadata": metadata if metadata else {}
        }

        db = MongoDBConnection.get_db()
        result = db["invoices"].insert_one(new_invoice_data)
        return result.inserted_id
    
    '''
    Updates an existing invoice with new data
    '''
    @staticmethod
    def update(invoice_id, update_data):
        
        if not invoice_id or not update_data:
            raise Exception("Error updating invoice, not enough data passed in")
        
        db = MongoDBConnection.get_db()
        result = db["invoices"].update_one(
            {"_id": ObjectId(invoice_id)},
            {"$set": update_data}
        )

        return result.modified_count > 0
    
    '''
    Gets all invoices for a specific user.
    '''
    @staticmethod
    def get_user_invoices(user_id: str, limit: int) -> List[dict]:
        if not User.exists(user_id):
            raise Exception("Get user invoices failed, user does not exist")
        
        db = MongoDBConnection.get_db()
        
        cursor = db["invoices"].find(
            {"user_id": user_id} 
        ).limit(limit).sort("created_at", -1)  # Sort by newest first
        
        result = list(cursor)
        
        # Return empty list instead of None to match return type annotation
        return result if result else []

    '''
    Gets user invoices filtered by type.
    '''
    @staticmethod
    def get_user_invoices_by_type(user_id: str, limit: int, type: str) -> List[dict]:
        if not User.exists(user_id):
            raise Exception("Get user invoices failed, user does not exist")

        db = MongoDBConnection.get_db()
        
        cursor = db["invoices"].find(
            {"user_id": user_id,
             "invoice_type": type
            } 
        ).limit(limit).sort("created_at", -1)  # Sort by newest first
        
        result = list(cursor)
        
        return result if result else []

    # ===== MARKETPLACE-SPECIFIC FUNCTIONS =====

    @staticmethod
    def generate_marketplace_invoice(buyer_id: str, seller_id: str, product_id: str, amount: float, fees: dict) -> str:
        """Generate comprehensive marketplace invoice with fee breakdown"""
        pass

    @staticmethod
    def calculate_tax_obligations(invoice_id: str, buyer_location: dict, seller_location: dict) -> dict:
        """Calculate tax obligations based on locations"""
        pass

    @staticmethod
    def get_seller_sales_report(seller_id: str, start_date: datetime, end_date: datetime) -> dict:
        """Generate sales report for seller"""
        pass

    @staticmethod
    def get_marketplace_revenue_report(start_date: datetime, end_date: datetime) -> dict:
        """Generate marketplace revenue report"""
        pass

    @staticmethod
    def export_invoices_for_accounting(user_id: str, format: str = "csv", year: int = None) -> dict:
        """Export invoices for accounting/tax purposes"""
        pass

    @staticmethod
    def void_invoice(invoice_id: str, reason: str, voider_id: str) -> bool:
        """Void an invoice"""
        pass

    @staticmethod
    def get_overdue_invoices(days_overdue: int = 30) -> List[dict]:
        """Get overdue invoices for collections"""
        pass

    @staticmethod
    def send_invoice_reminder(invoice_id: str, reminder_type: str) -> bool:
        """Send invoice payment reminder"""
        pass

    @staticmethod
    def apply_discount_to_invoice(invoice_id: str, discount_code: str, discount_amount: float) -> bool:
        """Apply discount to invoice"""
        pass

    @staticmethod
    def get_invoice_analytics(time_period: str = "30d") -> dict:
        """Get invoice analytics (paid vs unpaid, average amounts, etc.)"""
        pass

    @staticmethod
    def validate_invoice_data(invoice_data: dict) -> dict:
        """Validate invoice data for compliance"""
        pass

    @staticmethod
    def archive_old_invoices(cutoff_date: datetime) -> int:
        """Archive old invoices for storage optimization"""
        pass

    @staticmethod
    def get_tax_summary(user_id: str, tax_year: int) -> dict:
        """Get tax summary for user for specific year"""
        pass

    @staticmethod
    def flag_invoice_discrepancy(invoice_id: str, issue_type: str, flagger_id: str) -> str:
        """Flag invoice for discrepancy investigation"""
        pass

    @staticmethod
    def get_stripe_invoice(stripe_invoice_id: str) -> dict:
        """
        Retrieves invoice data from Stripe API
        """
        try:
            if not stripe_invoice_id:
                raise Exception("Stripe invoice ID is required")
            
            # Retrieve invoice from Stripe
            stripe_invoice = stripe.Invoice.retrieve(stripe_invoice_id)
            
            return stripe_invoice
            
        except stripe.error.InvalidRequestError as e:
            raise Exception(f"Invalid Stripe invoice ID: {e}")
        except stripe.error.AuthenticationError as e:
            raise Exception(f"Stripe authentication error: {e}")
        except stripe.error.APIConnectionError as e:
            raise Exception(f"Stripe API connection error: {e}")
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {e}")
        except Exception as e:
            raise Exception(f"Error retrieving Stripe invoice: {e}")

    @staticmethod
    async def handle_invoice_payment_succeeded(event_data: dict):
        """Handle invoice.payment_succeeded webhook event"""
        try:
            stripe_invoice_id = event_data.get("id")
            if not stripe_invoice_id:
                raise Exception("No invoice ID found in event data")

            # Check if we already have this invoice to avoid duplicates
            db = MongoDBConnection.get_db()
            existing_invoice = db["invoices"].find_one({
                "stripe_invoice_id": stripe_invoice_id
            })

            if existing_invoice:
                print(f"⚠️ Invoice already exists in database: {stripe_invoice_id}, skipping duplicate processing")
                return  # Skip processing if invoice already exists

            # Extract invoice data
            customer_id = event_data.get("customer")
            subscription_id = event_data.get("subscription")  # Will be present for subscription invoices
            amount_paid = event_data.get("amount_paid", 0)  # Amount in cents
            total_amount = event_data.get("total", 0)  # Total amount in cents
            currency = event_data.get("currency", "usd")
            created_timestamp = event_data.get("created", 0)
            paid_timestamp = event_data.get("status_transitions", {}).get("paid_at")
            
            # Customer information
            customer_email = event_data.get("customer_email", "")
            customer_name = event_data.get("customer_name", "")
            customer_address = event_data.get("customer_address")
            invoice_pdf = event_data.get("invoice_pdf", "")
            
            # Convert timestamps
            created_at = datetime.datetime.fromtimestamp(created_timestamp)
            paid_at = datetime.datetime.fromtimestamp(paid_timestamp) if paid_timestamp else created_at

            print(f"Processing invoice payment: {stripe_invoice_id}")
            print(f"Customer: {customer_id}, Subscription: {subscription_id}")
            print(f"Amount: ${amount_paid / 100}")

            # Determine if this is a subscription or product payment
            if subscription_id:
                # This is a subscription payment
                await Invoice._handle_subscription_invoice_payment(
                    stripe_invoice_id=stripe_invoice_id,
                    subscription_id=subscription_id,
                    customer_id=customer_id,
                    amount_paid=amount_paid,
                    created_at=created_at,
                    paid_at=paid_at,
                    customer_email=customer_email,
                    customer_name=customer_name,
                    customer_address=customer_address,
                    invoice_pdf=invoice_pdf,
                    event_data=event_data
                )
            else:
                # This might be a product payment, but likely already handled by checkout.session.completed
                print(f"📦 Product payment invoice detected: {stripe_invoice_id}")
                print(f"⚠️ Likely already processed via checkout.session.completed, skipping")
                # We skip product payments here since they're handled in checkout.session.completed
                return

            print(f"✅ Invoice payment processed successfully: {stripe_invoice_id}")
            
            return {
                "success": True,
                "stripe_invoice_id": stripe_invoice_id,
                "subscription_id": subscription_id,
                "amount_paid": amount_paid / 100
            }

        except Exception as e:
            print(f"❌ Error processing invoice payment: {e}")
            raise Exception(f"Error handling invoice payment succeeded: {e}")

    @staticmethod
    async def _handle_subscription_invoice_payment(
        stripe_invoice_id: str,
        subscription_id: str,
        customer_id: str,
        amount_paid: int,
        created_at: datetime.datetime,
        paid_at: datetime.datetime,
        customer_email: str,
        customer_name: str,
        customer_address: dict,
        invoice_pdf: str,
        event_data: dict
    ):
        """Handle subscription invoice payment processing"""
        try:
            # Find the subscription in our database
            db = MongoDBConnection.get_db()
            subscription = db["subscriptions"].find_one({
                "stripe_subscription_id": subscription_id
            })

            if not subscription:
                print(f"⚠️ Subscription not found in database: {subscription_id}")
                return

            user_id = subscription["user_id"]
            tier = subscription["tier"]

            # Create invoice record for this billing cycle
            invoice_id = Invoice.create(
                user_id=user_id,
                amount=amount_paid,
                stripe_invoice_id=stripe_invoice_id,
                type="subscription",
                paid_at=paid_at,
                payment_id=None,
                subscription_id=str(subscription["_id"]),
                seller_id=None,  # No seller for subscriptions
                product_id=None,  # No product for subscriptions
                metadata={
                    "tier": tier,
                    "customer_email": customer_email,
                    "customer_name": customer_name,
                    "customer_address": customer_address,
                    "invoice_pdf": invoice_pdf,
                    "billing_reason": event_data.get("billing_reason", "subscription_cycle"),
                    "period_start": event_data.get("period_start"),
                    "period_end": event_data.get("period_end")
                }
            )

            # Add transaction record to user
            db["users"].update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$push": {
                        "transactions": {
                            "type": "subscription",
                            "id": str(invoice_id),
                            "amount": amount_paid / 100,  # Convert from cents
                            "tier": tier,
                            "created_at": paid_at,
                            "stripe_invoice_id": stripe_invoice_id,
                            "stripe_subscription_id": subscription_id
                        }
                    }
                }
            )

            print(f"📄 Created subscription invoice: {invoice_id}")
            print(f"💰 Processed subscription payment for user: {user_id}, tier: {tier}")

        except Exception as e:
            print(f"❌ Error handling subscription invoice payment: {e}")
            raise
