PIPELINE_CONFIGS = {
    "v2": {
        "default_providers": {
            "text": "grok",
            "latex": "grok",
            "template": "grok"
        },
        "default_models": {
            "text": "grok-3-mini",
            "latex": "grok-3-mini",
            "template": "grok-3-mini"
        },
        "steps": ["text_generator", "latex_generator", "template_generator"]
    },
    "v3": {
        "default_providers": {
            "text": "openai",
            "latex": "grok"
        },
        "default_models": {
            "text": "gpt-4o-mini",
            "latex": "grok-3-mini",
        },
        "steps": ["text_generator", "latex_generator"]
    }   
}