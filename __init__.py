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
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE"}),  # Google Gemini API key
                "clip": ("CLIP",),  # CLIP model for text encoding
            }
        }

    RETURN_TYPES = ("CONDITIONING",)  # Output type for ComfyUI workflow
    FUNCTION = "enhance_prompt"  # Main function to execute
    CATEGORY = "conditioning"  # Node category in ComfyUI interface

    def enhance_prompt(self, text, api_key, clip):
        """
        Process the input prompt through Google Gemini and convert to CLIP conditioning.
        
        Args:
            text (str): The original prompt text to enhance
            api_key (str): Google Gemini API key
            clip: CLIP model for encoding text
            
        Returns:
            tuple: CLIP conditioning data suitable for Stable Diffusion
            
        Raises:
            ValueError: If API key is missing or invalid
        """
        # Validate API key is provided
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            raise ValueError("Google Gemini API key is missing or invalid. Please provide your API key.")

        try:
            # Configure the Google Generative AI SDK with provided API key
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-pro-exp-02-05')  

            # Add before API call:
            time.sleep(0.5)  # Brief pause to prevent rapid successive calls

            # Create a prompt template instructing Gemini how to enhance the text
            prompt_template = """
            You are a prompt engineer for Stable Diffusion XL.  
            Your task is to enhance and elaborate the following prompt for optimal image generation:

            Original Prompt: {user_prompt}

            Provide an enhanced prompt that includes specific details, artistic style, and visual elements to guide the image generation. Aim for around 50-100 words. Make it very descriptive.
            """

            # Fill in the template with user's prompt and send to Gemini
            full_prompt = prompt_template.format(user_prompt=text)
            response = model.generate_content(full_prompt)

            # Extract enhanced text from response or fallback to original
            if response.text:
                enhanced_prompt = response.text
                # Print the original and enhanced prompts to the console
                print("\n[Google AI Prompt Enhancer]")
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
        return ([[cond, {"pooled_output": pooled}]],)  # Return in ComfyUI conditioning format

# Register the node class for ComfyUI
NODE_CLASS_MAPPINGS = {
    "GoogleAIPromptEnhancer": GoogleAIPromptEnhancer
}

# Define the display name for the node in ComfyUI interface
NODE_DISPLAY_NAME_MAPPINGS = {
    "GoogleAIPromptEnhancer": "Google AI Prompt Enhancer"
}