from pipelines.base_pipeline import ResumePipelineBase
from build_latex.build import build_resumes
from models.chatgpt import *
from models.grok import *
from models.gemini import *
from models.claude import *
import logging


class V3Pipeline(ResumePipelineBase):
    def run_pipeline(self):
        text_result = self.run_text_generator()
        self.update_metrics(text_result)

        latex_result = self.run_latex_generator(text_result["responses"])
        self.update_metrics(latex_result)

        return build_resumes(latex_result["responses"], self.template_info[2])
    
    def run_text_generator(self):
        provider = self.config.get("default_providers").get("text") if self.data.get("text_provider") is None else self.data.get("text_provider")
        model = self.config.get("default_models").get("text") if self.data.get("text_model") is None else self.data.get("text_model")

        text_result = None
        plain_text_prompt = self.get_system_prompts()[0]
        user_prompt = f"Here is the user data: {self.data.get('user_data') if self.data.get('type') == 'upload' else self.data.get('new_resume_data')}"
        logging.info(f"Running v3 text generator({provider}, {model})...")
        match provider:
            case "openai":
                text_result = run_chatgpt_model(plain_text_prompt, user_prompt, model, n=1)
            case "grok":
                text_result = run_grok_model(plain_text_prompt, user_prompt, model, n=1)
            case "gemini":
                text_result = run_gemini_model(plain_text_prompt, user_prompt, model, n=1)
            case "claude":
                text_result = run_claude_model(plain_text_prompt, user_prompt, model, n=1)
            case _:
                raise ValueError(f"Invalid provider: {provider}")
            
        if not isinstance(text_result, list):
            text_result = [text_result]
            
        # Calculate pricing
        total_input_tokens = sum(res["prompt_tokens"] for res in text_result)
        total_output_tokens = sum(res["completion_tokens"] for res in text_result)
        pricing = self.get_pricing(provider, model, total_input_tokens, total_output_tokens)
            
        return {
            "responses": text_result,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "pricing": pricing
        }
    
    def run_latex_generator(self, text_responses):
        provider = self.config.get("default_providers").get("latex") if self.data.get("latex_provider") is None else self.data.get("latex_provider")
        model = self.config.get("default_models").get("latex") if self.data.get("latex_model") is None else self.data.get("latex_model")

        latex_result = None
        plain_to_latex_prompt = self.get_system_prompts()[1]
        user_prompt = f"Here is the text to transform into latex: {text_responses}"
        logging.info(f"Running v3 latex generator({provider}, {model})...")
        match provider:
            case "openai":
                latex_result = run_chatgpt_model(plain_to_latex_prompt, user_prompt, model, n=3)
            case "grok":
                latex_result = run_grok_model(plain_to_latex_prompt, user_prompt, model, n=3)
            case "gemini":
                latex_result = run_gemini_model(plain_to_latex_prompt, user_prompt, model, n=3)
            case "claude":
                latex_result = run_claude_model(plain_to_latex_prompt, user_prompt, model, n=3)
            case _:
                raise ValueError(f"Invalid provider: {provider}")
            
        if not isinstance(latex_result, list):
            latex_result = [latex_result]
            
        total_input_tokens = sum(res["prompt_tokens"] for res in latex_result)
        total_output_tokens = sum(res["completion_tokens"] for res in latex_result)
        pricing = self.get_pricing(provider, model, total_input_tokens, total_output_tokens)

        return {
            "responses": latex_result,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "pricing": pricing
        }
    
    def get_system_prompts(self):
        with open("prompts/v3/generate_plain_text.txt") as f:
            plain_text_prompt = "".join(f.readlines())
        with open("prompts/v3/generate_latex.txt") as f:
            plain_to_latex_prompt = "".join(f.readlines())
        return plain_text_prompt, plain_to_latex_prompt
    
    def get_models_list(self):
        return [
            self.config.get("default_providers").get("text") if self.data.get("text_provider") is None else self.data.get("text_provider"),
            self.config.get("default_models").get("text") if self.data.get("text_model") is None else self.data.get("text_model"),
            self.config.get("default_providers").get("latex") if self.data.get("latex_provider") is None else self.data.get("latex_provider"),
            self.config.get("default_models").get("latex") if self.data.get("latex_model") is None else self.data.get("latex_model")
        ]
    
    def get_pricing(self, provider, model, input_tokens, output_tokens):
        match provider:
            case "openai":
                return get_chatgpt_pricing(input_tokens, output_tokens, model)["total_cost"]
            case "grok":
                return get_grok_pricing(input_tokens, output_tokens, model)["total_cost"]
            case "gemini":
                return get_gemini_pricing(input_tokens, output_tokens, model)["total_cost"]
            case "claude":
                return get_claude_pricing(input_tokens, output_tokens, model)["total_cost"]
            case _:
                raise ValueError(f"Invalid provider: {provider}")
            

    
