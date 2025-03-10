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
        pass

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
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING")  # Output types for positive and negative conditioning
    RETURN_NAMES = ("positive", "negative")  # Name the outputs for clarity
    FUNCTION = "enhance_prompt"  # Main function to execute
    CATEGORY = "conditioning"  # Node category in ComfyUI interface

    def enhance_prompt(self, text, api_key, model, clip, negative_text=""):
        """
        Process the input prompt through Google Gemini and convert to CLIP conditioning.
        Also process negative prompt separately (without enhancement).
        
        Args:
            text (str): The original prompt text to enhance
            api_key (str): Google Gemini API key
            model (str): The Google Gemini model to use
            clip: CLIP model for encoding text
            negative_text (str): Negative prompt text (not enhanced through AI)
            
        Returns:
            tuple: Tuple containing positive and negative CLIP conditioning data
        """
        # Validate API key is provided
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            raise ValueError("Google Gemini API key is missing or invalid. Please provide your API key.")

        # Process positive prompt
        try:
            # Configure the Google Generative AI SDK with provided API key
            genai.configure(api_key=api_key)
            model_instance = genai.GenerativeModel(model)  

            # Add before API call:
            time.sleep(0.5)  # Brief pause to prevent rapid successive calls

            # Create a prompt template instructing Gemini how to enhance the text
            # Updated to request unique variations
            prompt_template = """
            You are a prompt engineer for Stable Diffusion XL.  
            Your task is to enhance and elaborate the following prompt for optimal image generation:

            Original Prompt: {user_prompt}

            Create a unique variation of an enhanced prompt that includes specific details, artistic style, and visual elements.
            Each time this is called, you should generate a DIFFERENT interpretation or angle on the original prompt.
            Add different styles, lighting, composition, or details to ensure variety.
            Aim for around 50-100 words. Make it very descriptive.
            
            Important: This is part of a batch generation process, so make this interpretation noticeably different from other possible interpretations.
            Only output the prompt text, no other details, no explainations or additional information or commentary.
            """

            # Add a small random element to ensure uniqueness in API calls
            import random
            variation_seed = random.randint(1, 10000)
            
            # Fill in the template with user's prompt and send to Gemini
            full_prompt = prompt_template.format(user_prompt=text) + f"\nUnique variation #{variation_seed}. Make this truly distinct."
            response = model_instance.generate_content(full_prompt)

            # Extract enhanced text from response or fallback to original
            if response.text:
                enhanced_prompt = response.text
                # Print the original and enhanced prompts to the console
                print("\n[Google AI Prompt Enhancer]")
                print(f"Model: {model}")
                print(f"Variation: #{variation_seed}")
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
        
        # Return both positive and negative conditioning
        return ([[cond, {"pooled_output": pooled}]],
                [[neg_cond, {"pooled_output": neg_pooled}]])
        
# Register the node class for ComfyUI
NODE_CLASS_MAPPINGS = {
    "GoogleAIPromptEnhancer": GoogleAIPromptEnhancer
}

# Define the display name for the node in ComfyUI interface
NODE_DISPLAY_NAME_MAPPINGS = {
    "GoogleAIPromptEnhancer": "Google AI Prompt Enhancer"
}