import logging
from pipelines.base_pipeline import ResumePipelineBase
from routes.create_v2 import (
    run_text_generator, run_latex_generator, run_template_generator
)
from build_latex.build import build_resumes

class V2Pipeline(ResumePipelineBase):
    def run_pipeline(self):
        """3-step pipeline: text → latex → template"""
        # Step 1: Text generation
        text_result = self.run_text_generator()
        self.update_metrics(text_result)
        
        # Step 2: LaTeX generation  
        latex_result = self.run_latex_generator(text_result["responses"])
        self.update_metrics(latex_result)
        
        # Step 3: Template transformation
        template_result = self.run_template_generator(latex_result["responses"])
        self.update_metrics(template_result)
        
        # Step 4: Build resumes
        return build_resumes(template_result["responses"], self.template_info[2])
    
    def run_text_generator(self):
        """Run text generation step"""
        provider = self.config.get("default_providers").get("text") if self.data.get("text_provider") is None else self.data.get("text_provider")
        model = self.config.get("default_models").get("text") if self.data.get("text_model") is None else self.data.get("text_model")
        
        # Choose user data based on type
        if self.data.get("type") == "upload":
            user_data = self.data.get("user_data")
        else:
            user_data = self.data.get("new_resume_data")
            
        tailor_information = self.data.get("tailor_data")
        
        logging.info(f"Running text generator ({provider}, {model})...")
        return run_text_generator(provider, model, user_data, tailor_information)
    
    def run_latex_generator(self, text_responses):
        """Run LaTeX generation step""" 
        provider = self.config.get("default_providers").get("latex") if self.data.get("latex_provider") is None else self.data.get("latex_provider")
        model = self.config.get("default_models").get("latex") if self.data.get("latex_model") is None else self.data.get("latex_model")
        
        logging.info(f"Running latex generator ({provider}, {model})...")
        return run_latex_generator(provider, model, text_responses)
    
    def run_template_generator(self, latex_responses):
        """Run template transformation step"""
        provider = self.config.get("default_providers").get("template") if self.data.get("template_provider") is None else self.data.get("template_provider")
        model = self.config.get("default_models").get("template") if self.data.get("template_model") is None else self.data.get("template_model")
        
        template_latex = self.template_info[1]  # template_latex from get_template_latex
        
        logging.info(f"Running template transformer ({provider}, {model})...")
        return run_template_generator(provider, model, latex_responses, template_latex)
    
    def get_models_list(self):
        """Return list of models used for logging"""
        return [
            self.config.get("default_providers").get("text") if self.data.get("text_provider") is None else self.data.get("text_provider"),
            self.config.get("default_models").get("text") if self.data.get("text_model") is None else self.data.get("text_model"),
            self.config.get("default_providers").get("latex") if self.data.get("latex_provider") is None else self.data.get("latex_provider"),
            self.config.get("default_models").get("latex") if self.data.get("latex_model") is None else self.data.get("latex_model"),
            self.config.get("default_providers").get("template") if self.data.get("template_provider") is None else self.data.get("template_provider"),
            self.config.get("default_models").get("template") if self.data.get("template_model") is None else self.data.get("template_model")
        ]