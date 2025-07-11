import logging
import time
import shutil
import os
from templates.templates import get_template_latex
from build_latex.build import build_resumes
from database.database import database_init

class ResumePipelineBase:
    def __init__(self, data, config):
        self.data = data
        self.config = config
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.start_time = time.time()
        self.template_info = None
        self.final_names = []

    def execute(self):
        """Template method - defines the common flow"""
        logging.info(f"Running pipeline...")
        self.validate_data()
        self.clean_data()
        self.setup_template()
        result = self.run_pipeline()  # Abstract method implemented by subclasses
        self.post_process(result)
        self.save_results()
        return result
    
    def validate_data(self):
        """Validate required fields are present"""
        required_fields = ["user_id", "template_data", "type"]
        for field in required_fields:
            if not self.data.get(field):
                raise ValueError(f"Missing required field: {field}")
    
    def clean_data(self):
        """Clean new resume data of empty/null fields"""
        new_resume_data = self.data.get("new_resume_data")
        if new_resume_data and isinstance(new_resume_data, dict):
            # Remove empty values
            new_resume_data = {k: v for k, v in new_resume_data.items() if v not in [None, "", [], {}]}
            
            # Clean nested list items
            for key, value in new_resume_data.items():
                if isinstance(value, list):
                    new_resume_data[key] = [
                        {k: v for k, v in item.items() if v not in [None, "", [], {}]} 
                        if isinstance(item, dict) else item 
                        for item in value 
                        if item not in [None, "", [], {}]
                    ]
            
            self.data["new_resume_data"] = new_resume_data

    def setup_template(self):
        """Initialize template information"""
        template_selection = self.data.get("template_data")
        self.template_info = get_template_latex(template_selection)
        
    def post_process(self, result):
        """Log metrics and filter successful results"""
        names, results = result
        
        # Filter successful builds
        self.final_names = [name for name, res in zip(names, results) if res]
        
        # Log metrics
        logging.info(f"Names: {','.join(self.final_names)}")
        logging.info(f"Total Input tokens: {self.total_input_tokens}")
        logging.info(f"Total Output tokens: {self.total_output_tokens}")
        logging.info(f"Total Cost: {self.total_cost}")
        
    def save_results(self):
        """Save to database and copy files if in dev mode"""
        
        end_time = time.time()
        total_time = end_time - self.start_time
            
        # Prepare database entry
        user_id = self.data.get("user_id")
        type_val = self.data.get("type")
        template_selection = self.data.get("template_data")
        tailor_information = self.data.get("tailor_data")
        models = self.get_models_list()
            
        # Insert into database
        db = database_init()
        db.cursor().execute("""
                INSERT INTO testing (user_id, type, models, template_name, input_tokens, 
                                   output_tokens, time_taken, files_names, files_scored, 
                                   total_tokens, total_price, scores, final_score, job_description) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, type_val, ','.join(models), template_selection, 
                self.total_input_tokens, self.total_output_tokens, total_time, 
                ','.join(self.final_names), '', 
                self.total_input_tokens + self.total_output_tokens, 
                self.total_cost, ','.join([str(0)] * len(self.final_names)), 
                0, tailor_information
            ))
        db.commit()
        db.close()
            
        # Copy files to test directory
        if self.data.get("dev_mode"):
            project_root = os.path.dirname(os.path.dirname(__file__))
            for name in self.final_names:
                src = os.path.join(project_root, "data", "resumes", f"{name}.pdf")
                dst = os.path.join(project_root, "data", "test", f"{name}.pdf")
                
                # Add safety check
                if os.path.exists(src):
                    shutil.copy2(src, dst)
                    logging.info(f"Copied {name}.pdf to test directory")
                else:
                    logging.warning(f"Source file not found: {src}")

    def get_models_list(self):
        """Get list of models used - implemented by subclasses"""
        return []
        
    def run_pipeline(self):
        """Abstract method - each version implements their own pipeline"""
        raise NotImplementedError("Subclasses must implement run_pipeline")

    def update_metrics(self, response):
        """Helper to update token counts and costs"""
        self.total_input_tokens += response.get("input_tokens", 0)
        self.total_output_tokens += response.get("output_tokens", 0)
        self.total_cost += response.get("pricing", 0.0)
