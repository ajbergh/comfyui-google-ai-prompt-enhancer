"""
ComfyUI Google AI Prompt Enhancer Extension
==========================================

This extension provides a node for ComfyUI that enhances image generation prompts 
using Google's Generative AI (Gemini) model. The node takes a user prompt and 
API key as input, sends the prompt to Google's Gemini API for enhancement, and 
returns the enhanced prompt as conditioning for a Stable Diffusion model.

Features:
- Connects to Google Gemini API to enhance text prompts
- Converts enhanced prompts to CLIP token embeddings for image generation
- Handles errors gracefully with appropriate fallbacks
- Provides clear feedback on API connection issues

Requirements:
- google-generativeai Python package
- Valid Google Gemini API key
- ComfyUI environment

Author: Adam Bergh
License: MIT
"""

# Try to import required packages with helpful error messages
try:
    import google.generativeai as genai  # Google's Generative AI Python SDK
except ImportError:
    print("Error: Google Generative AI package not found. Please install with:")
    print("pip install google-generativeai")
    raise

import comfy.sd  # ComfyUI's stable diffusion utilities
import torch  # PyTorch for tensor operations
import time  # Time module for sleep function

class GoogleAIPromptEnhancer:
    """
    A ComfyUI node that enhances prompts using Google's Gemini AI.
    
    This node sends the user's text prompt to Gemini API, which returns an enhanced
    version with more descriptive details suitable for image generation.
    """
    
    def __init__(self):
        """Initialize the node with default values.""" 
        # Store a seed that changes on each instance creation
        self.instance_creation_time = time.time()
    
    @classmethod
    def INPUT_TYPES(s):
        """
        Define the input parameters for the node.
        
        Returns:
            dict: Dictionary specifying required and optional inputs with their types and defaults
        """
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": "A beautiful landscape"}),  # User's input prompt
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "password": True}),  # Google Gemini API key with password flag
                "model": (["gemini-2.0-pro-exp-02-05", "gemini-2.0-flash-thinking-exp-01-21", 
                           "gemini-2.0-flash-exp", "gemini-2.0-flash"], {"default": "gemini-2.0-pro-exp-02-05"}),  # Model selection
                "clip": ("CLIP",),  # CLIP model for text encoding
                "negative_text": ("STRING", {"multiline": True, "default": ""}),  # Negative prompt text
                "seed_override": ("INT", {"default": 0, "min": 0, "max": 1000000000}),  # Add a seed override input
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "INT")  # Added INT return type for seed
    RETURN_NAMES = ("positive", "negative", "seed")  # Added seed return name
    FUNCTION = "enhance_prompt"  # Main function to execute
    CATEGORY = "conditioning"  # Node category in ComfyUI interface

    def enhance_prompt(self, text, api_key, model, clip, negative_text="", seed_override=0):
        """
        Process the input prompt through Google Gemini and convert to CLIP conditioning.
        Also process negative prompt separately (without enhancement).
        
        Args:
            text (str): The original prompt text to enhance
            api_key (str): Google Gemini API key
            model (str): The Google Gemini model to use
            clip: CLIP model for encoding text
            negative_text (str): Negative prompt text (not enhanced through AI)
            seed_override (int): Optional seed override for uniqueness
            
        Returns:
            tuple: Tuple containing positive and negative CLIP conditioning data and seed
        """
        # Validate API key is provided
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            raise ValueError("Google Gemini API key is missing or invalid. Please provide your API key.")

        # Generate a truly unique seed for this specific run
        import random
        import datetime
        import uuid
        import os

        # Combine multiple sources of randomness
        if seed_override > 0:
            # Use user-provided seed if available
            variation_seed = seed_override
        else:
            # Generate a completely unique seed combining multiple entropy sources
            current_time = time.time() * 1000  # millisecond precision
            pid = os.getpid()
            random_component = random.randint(1, 1000000)
            instance_component = int(self.instance_creation_time * 1000) % 1000000
            unique_id = str(uuid.uuid4().int)[:8]  # Use part of a UUID for additional randomness
            
            # Combine all sources into a single integer
            variation_seed = int(f"{int(current_time % 10000)}{pid % 100}{random_component % 10000}{instance_component % 1000}{int(unique_id) % 10000}") % 1000000000

        # Process positive prompt
        try:
            # Configure the Google Generative AI SDK with provided API key
            genai.configure(api_key=api_key)
            model_instance = genai.GenerativeModel(model)  

            # Add before API call:
            time.sleep(0.5)  # Brief pause to prevent rapid successive calls

            # Create timestamp for this specific call
            timestamp = datetime.datetime.now().isoformat()
            
            # Insert the variation seed directly into the prompt to ensure uniqueness
            unique_text = f"{text} [UNIQUENESS_MARKER_{timestamp}_{variation_seed}]"
            
            # Create a prompt template instructing Gemini how to enhance the text
            prompt_template = """
            You are a prompt engineer for Stable Diffusion XL.  
            Your task is to enhance and elaborate the following prompt for optimal image generation:

            Original Prompt: {user_prompt}

            IMPORTANT: Your response MUST be a NEW and UNIQUE variation each time. 
            Create a completely different interpretation with:
            - Different artistic style than you would typically suggest
            - Unique lighting conditions
            - Alternative composition approach
            - Varied details and elements
            
            This is variation #{seed} in a batch generation process.
            
            Aim for around 50-100 words. Make it very descriptive.
            Only output the enhanced prompt text, no explanations or commentary.
            Ignore any UNIQUENESS_MARKER tags in the prompt.
            """
            
            # Fill in the template with user's prompt and seed
            full_prompt = prompt_template.format(user_prompt=unique_text, seed=variation_seed)
            # Add extra uniqueness forcing parameters
            full_prompt += f"\n\nUnique variation #{variation_seed} @ {timestamp}. Make this absolutely distinct from all other variations."
            
            # Create generation config with temperature to increase variation
            generation_config = {
                "temperature": 0.9,  # Increase randomness
                "top_p": 0.95,       # Sample from more diverse options
            }
            
            # Call the API with the generation config
            response = model_instance.generate_content(
                full_prompt,
                generation_config=generation_config
            )

            # Extract enhanced text from response or fallback to original
            if response.text:
                enhanced_prompt = response.text.replace(f"[UNIQUENESS_MARKER_{timestamp}_{variation_seed}]", "").strip()
                # Print the original and enhanced prompts to the console
                print("\n[Google AI Prompt Enhancer]")
                print(f"Model: {model}")
                print(f"Run ID: {variation_seed}")
                print(f"Original prompt: {text}")
                print(f"Enhanced prompt: {enhanced_prompt}\n")
            else:
                enhanced_prompt = text  # Fallback to the original prompt if no enhancement
                print("Warning: Gemini did not return an enhanced prompt. Using the original prompt.")
        except Exception as e:
            # More specific error message categorization
            if "API key" in str(e).lower():
                print(f"Error: Invalid Google Gemini API key. Please check your key. Details: {e}")
            elif "quota" in str(e).lower():
                print(f"Error: API quota exceeded. Details: {e}")
            else:
                print(f"Error during Gemini API call: {e}")
            enhanced_prompt = text  # Fallback to original prompt on error

        # Convert the prompt text to CLIP conditioning format
        tokens = clip.tokenize(enhanced_prompt)  # Convert text to tokens
        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)  # Encode tokens to embeddings
        
        # Process negative prompt (directly, without enhancement)
        neg_tokens = clip.tokenize(negative_text)
        neg_cond, neg_pooled = clip.encode_from_tokens(neg_tokens, return_pooled=True)
        
        # Return both positive and negative conditioning, plus the seed used
        return ([[cond, {"pooled_output": pooled}]],
                [[neg_cond, {"pooled_output": neg_pooled}]],
                variation_seed)
        
    # Add this property to tell ComfyUI to never cache the results of this node
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Tell ComfyUI this node always changes, preventing result caching.
        
        This forces ComfyUI to re-execute this node on each run, even in batched queue operations.
        """
        # Return current time to ensure the node is always considered "changed"
        return time.time()

# Register the node class for ComfyUI
NODE_CLASS_MAPPINGS = {
    "GoogleAIPromptEnhancer": GoogleAIPromptEnhancer
}

# Define the display name for the node in ComfyUI interface
NODE_DISPLAY_NAME_MAPPINGS = {
    "GoogleAIPromptEnhancer": "Google AI Prompt Enhancer"
}