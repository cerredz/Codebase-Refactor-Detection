from typing import List, Tuple, Dict
from bson import ObjectId
from backend.models.Workflow import WorkflowModel
from backend.services.User import User
from backend.services.Product import Product
from backend.services.Store import Store
from backend.services.transactions.Subscriptions import Subscription
from backend.lib.Mongo import MongoDBConnection
from backend.middleware.user.User import UserMiddleware
# Import middleware
from backend.middleware.workflow.Workflow import create_workflow_middleware, read_workflow_middleware
import os
import json
import datetime
import hashlib

class Workflow:

    @staticmethod
    def exists(workflow_id):
        if not workflow_id:
            raise Exception("Workflow is not passed in.")
        
        db = MongoDBConnection.get_db()
        workflow = db["workflows"].find_one({"_id": ObjectId(workflow_id)})

        if not workflow or len(workflow) == 0:
            return False
        
        return True
    
    @staticmethod
    @read_workflow_middleware
    def get(workflow_id: str, user_id: str = None) -> dict:
        """Returns same data that goes into mongodb"""
        db = MongoDBConnection.get_db()
        workflow = db["workflows"].find_one({"_id": ObjectId(workflow_id)})
        if not workflow:
            return None
        
        workflow_model = WorkflowModel(**workflow)
        return {**workflow_model.model_dump()}

    @staticmethod
    @create_workflow_middleware
    @UserMiddleware.validate_user_exists
    def create_workflow(
        user_id: str, 
        store_id: str,
        product_id: str, 
        workflow_definition: Dict[str], 
        nodes: List[dict] = None, 
        is_validated: bool = False, 
        validation_errors: List = None, 
        file_size: int = None,
        # Added by middleware
        calculated_file_hash: str = None,
        structural_file_hash: str = None,
        calculated_file_size: int = None,
        json_security_metrics: dict = None
    ) -> str:
        """
h full security validation.        Create a new workflow wit
        
        Args:
            user_id: ID of the user creating the workflow
            store_id: ID of the store the workflow belongs to
            product_id: ID of the product the workflow is for
            workflow_definition: The n8n workflow JSON definition
            nodes: List of node metadata (optional)
            is_validated: Whether the workflow has been validated
            validation_errors: List of validation errors (optional)
            file_size: Size of the workflow file (optional - calculated by middleware)
            
        Middleware-added parameters:
            calculated_file_hash: Hash calculated by uniqueness middleware
            structural_file_hash: Structural hash calculated by uniqueness middleware  
            calculated_file_size: File size calculated by size limit middleware
            json_security_metrics: Security metrics from JSON sanitization
        
        Returns:
            str: The created workflow ID
        """
        # Make sure there is not already a workflow for this product
        if not Product.exists(product_id) or not Store.exists(store_id):
            raise Exception("Cannot create workflow, product/store does not exist")
        
        existing_workflow_id = Product.get(product_id).get("workflow_id")
        if existing_workflow_id:
            raise Exception("Cannot create workflow, this product already has one")
        
        # Make sure user has active subscription (redundant check but good to have)
        user_info = User.get_user_info(user_id)
        user_subscription = user_info.get("subscription")

        if not User.has_active_subscription(user_id):
            raise Exception("User cannot make a workflow, they do not have a valid subscription")

        subscription_data = Subscription.get(user_subscription)
        tier = subscription_data.get("tier", "standard")
        user_tier = "enterprise" if tier == "enterprise" else "standard"
        
        # Use hashes calculated by middleware
        file_hash = calculated_file_hash
        structural_hash = structural_file_hash
        actual_file_size = calculated_file_size or file_size
        
        # Create and save the workflow file
        file_dest = Workflow._create_workflow_file(user_tier, workflow_definition, product_id, file_hash)
                
        # Create workflow document (NO workflow_definition stored in DB - ONLY METADATA)
        new_workflow = {
            "user_id": user_id,
            "product_id": product_id,
            "store_id": store_id,
            "nodes": nodes or [],  # Default to empty list if not provided
            "created_at": datetime.datetime.now(),
            "is_validated": is_validated,
            "validation_errors": validation_errors or [],
            "file_size": actual_file_size,
            "file_hash": file_hash,
            "structural_hash": structural_hash,  # Add structural hash
            "file_dest": file_dest,
            # Add security metrics for monitoring
            "security_metrics": json_security_metrics or {}
        }

        new_workflow = WorkflowModel(**new_workflow)
        
        # Insert workflow into database
        db = MongoDBConnection.get_db()
        result = db["workflows"].insert_one(new_workflow)
        workflow_id = str(result.inserted_id)
        
        # Update product with workflow_id
        Product.update_product_info(product_id, {
            "workflow_id": workflow_id,
        })
        
        return workflow_id
    
    @staticmethod
    @create_workflow_middleware
    def _create_workflow_file(user_tier: str, workflow_definition: dict, product_id: str, file_hash: str) -> str:
        """Private method to create workflow file on disk"""
        stan_rel_path = "workflows/standard"
        enter_rel_path = "workflows/enterprise"
        base_path = enter_rel_path if user_tier == "enterprise" else stan_rel_path
        
        # Ensure directory exists
        os.makedirs(base_path, exist_ok=True)
        
        # Create filename with hash
        file_name = f"workflow_{product_id}_{file_hash[:8]}.json"
        file_dest = os.path.join(base_path, file_name)
        
        # Save workflow file to destination
        try:
            with open(file_dest, 'w') as json_file:
                json.dump(workflow_definition, json_file, indent=4)
        except Exception as e:
            raise Exception(f"Failed to save workflow file: {e}")
        
        return file_dest

    @staticmethod
    def create_from_json(user_tier, workflow_definition, product_id):
        """Legacy method - kept for backward compatibility"""
        workflow_content = json.dumps(workflow_definition, sort_keys=True)
        file_hash = hashlib.sha256(workflow_content.encode()).hexdigest()
        file_dest = Workflow._create_workflow_file(user_tier, workflow_definition, product_id, file_hash)
        return file_hash, file_dest
    
    def extract_metadata(self) -> dict:
        # TODO: Implement metadata extraction
        pass

    def detect_platform(workflow_json: dict) -> str:
        """Auto-detect platform and update product.platform"""
        # TODO: Implement platform detection
        pass

    def sync_to_product(self):
        """Update product's supported_triggers, platform from workflow metadata"""
        # TODO: Implement product sync
        pass

    @staticmethod
    @read_workflow_middleware
    def export_for_buyer(workflow_id: str, user_id: str = None) -> dict:
        """Export the original workflow JSON for buyer download"""
        if not Workflow.exists(workflow_id):
            raise Exception("Error exporting workflow to buyer, workflow does not exist.")
        
        # Get the workflow data from database
        workflow_data = Workflow.get(workflow_id, user_id)
        
        # Get the saved file path and hash
        file_dest = workflow_data.get("file_dest")
        file_hash = workflow_data.get("file_hash")
        product_id = workflow_data.get("product_id")
        
        # Read the workflow from the saved file
        try:
            with open(file_dest, 'r') as json_file:
                workflow_definition = json.load(json_file)
        except Exception as e:
            raise Exception(f"Failed to read workflow file: {e}")
        
        # Create export filename for buyer
        buyer_filename = f"automation_{product_id}.json"
        
        return {
            "workflow_definition": workflow_definition,
            "file_path": file_dest,
            "download_filename": buyer_filename,
            "product_id": product_id,
            "workflow_id": workflow_id,
            "file_hash": file_hash
        }

    # ===== MARKETPLACE-SPECIFIC FUNCTIONS =====

    @staticmethod
    def validate_workflow_integrity(workflow_id: str) -> dict:
        """Validate workflow file integrity and detect corruption"""
        pass

    @staticmethod
    def analyze_workflow_complexity(workflow_definition: dict) -> dict:
        """Analyze workflow complexity metrics (nodes, connections, depth)"""
        pass

    @staticmethod
    def extract_workflow_metadata(workflow_definition: dict) -> dict:
        """Extract metadata from workflow (supported platforms, triggers, etc.)"""
        pass

    @staticmethod
    def get_workflow_performance_stats(workflow_id: str) -> dict:
        """Get workflow download stats, user feedback, performance metrics"""
        pass

    @staticmethod
    def create_workflow_backup(workflow_id: str, backup_reason: str = "manual") -> str:
        """Create backup copy of workflow"""
        pass

    @staticmethod
    def restore_workflow_from_backup(workflow_id: str, backup_id: str) -> bool:
        """Restore workflow from backup"""
        pass

    @staticmethod
    def validate_n8n_compatibility(workflow_definition: dict, n8n_version: str = "latest") -> dict:
        """Validate workflow compatibility with n8n versions"""
        pass

    @staticmethod
    def scan_for_sensitive_data(workflow_definition: dict) -> dict:
        """Scan workflow for sensitive data (API keys, credentials, PII)"""
        pass

    @staticmethod
    def optimize_workflow_size(workflow_definition: dict) -> dict:
        """Optimize workflow JSON size while preserving functionality"""
        pass

    @staticmethod
    def get_workflow_dependencies(workflow_definition: dict) -> List[str]:
        """Extract workflow dependencies (required services, APIs, etc.)"""
        pass

    @staticmethod
    def test_workflow_connectivity(workflow_definition: dict) -> dict:
        """Test if workflow has proper node connections and flow"""
        pass

    @staticmethod
    def generate_workflow_preview(workflow_definition: dict) -> dict:
        """Generate visual preview data for workflow display"""
        pass

    @staticmethod
    def convert_workflow_format(workflow_definition: dict, target_format: str) -> dict:
        """Convert between different automation platforms (n8n, Zapier, etc.)"""
        pass

    @staticmethod
    def get_similar_workflows(workflow_id: str, similarity_threshold: float = 0.8, limit: int = 10) -> List[dict]:
        """Find similar workflows based on structure and functionality"""
        pass

    @staticmethod
    def flag_workflow_issue(workflow_id: str, issue_type: str, reporter_id: str, details: str) -> str:
        """Flag workflow for issues (malware, policy violation, etc.)"""
        pass

    @staticmethod
    def moderate_workflow(workflow_id: str, action: str, moderator_id: str, reason: str = "") -> bool:
        """Moderate workflow (approve, quarantine, delete)"""
        pass

    @staticmethod
    def get_workflow_usage_analytics(workflow_id: str, time_period: str = "30d") -> dict:
        """Get workflow download and usage analytics"""
        pass

    @staticmethod
    def create_workflow_changelog(workflow_id: str, changes: dict, version: str) -> str:
        """Create changelog entry for workflow updates"""
        pass

    @staticmethod
    def get_workflow_changelog(workflow_id: str) -> List[dict]:
        """Get complete changelog for workflow"""
        pass

    @staticmethod
    def compress_workflow_file(workflow_id: str) -> dict:
        """Compress workflow file for storage optimization"""
        pass

    @staticmethod
    def decompress_workflow_file(workflow_id: str) -> dict:
        """Decompress workflow file for use"""
        pass

