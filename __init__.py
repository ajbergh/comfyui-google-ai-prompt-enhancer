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
import random
import datetime
import uuid
import os

class GoogleAIPromptEnhancer:
    """
    A ComfyUI node that enhances prompts using Google's Gemini AI.

    This node sends the user's text prompt to Gemini API, which returns an enhanced
    version with more descriptive details suitable for image generation.

    New Feature:
    - 'Model Type' dropdown lets you select the target Stable Diffusion model (SD1.5, SDXL, Flux, Flux Kontext, WAN 2.2).
    - The selected model type influences the system prompt sent to Gemini, optimizing the enhanced prompt for your chosen model.
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
        # Define the default negative prompt for SDXL, which is the default model_type
        sdxl_negative_prompt = "low detail, distorted anatomy, unrealistic proportions, washed out colors, overexposed, watermark, text, bad hands, extra limbs, blurry background, chromatic aberration"

        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": "A beautiful landscape"}),  # User's input prompt
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "password": True}),  # Google Gemini API key
                "model": (["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-exp", "gemini-2.0-flash", "gemini-2.0-flash-exp-image-generation"], {"default": "gemini-2.0-pro-exp-02-05"}),  # Model selection
                "model_type": (["SD1.5", "SDXL", "Flux", "Flux Kontext", "WAN 2.2"], {"default": "SDXL"}),  # Model dropdown
                "clip": ("CLIP",),  # CLIP model for text encoding
                "negative_text": ("STRING", {"multiline": True, "default": sdxl_negative_prompt, "description": "Pre-populated based on model type"}),  # Negative prompt text
                "creativity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}), # Creativity (temperature)
                "seed_override": ("INT", {"default": 0, "min": 0, "max": 1000000000}),  # Seed override
            },
            "optional": {
                "keep_concise": ("BOOLEAN", {"default": False}), # Add conciseness checkbox
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "INT", "STRING")  # Added STRING return type
    RETURN_NAMES = ("positive", "negative", "seed", "enhanced_prompt")  # Added enhanced_prompt return
    FUNCTION = "enhance_prompt"  # Main function to execute
    CATEGORY = "conditioning"  # Node category in ComfyUI interface

    def enhance_prompt(self, text, api_key, model, model_type, clip, creativity, negative_text="", seed_override=0, keep_concise=False):
        """
        Process the input prompt through Google Gemini and convert to CLIP conditioning.
        Also process negative prompt separately (without enhancement).
        
        Args:
            text (str): The original prompt text to enhance
            api_key (str): Google Gemini API key
            model (str): The Google Gemini model to use
            model_type (str): The type of Stable Diffusion model (e.g., SD1.5, SDXL)
            clip: CLIP model for encoding text
            creativity (float): The temperature for the Gemini model
            negative_text (str): Negative prompt text (not enhanced through AI)
            seed_override (int): Optional seed override for uniqueness
            keep_concise (bool): Whether to keep the enhanced prompt concise
            
        Returns:
            tuple: Tuple containing positive and negative CLIP conditioning, seed, and enhanced prompt text
        """
        # Model-specific default negative prompts
        model_negative_presets = {
            "SD1.5": "blurry, lowres, bad anatomy, extra limbs, poorly drawn hands, fused fingers, mutated hands, deformed face, long neck, watermark, text, logo, grainy, jpeg artifacts",
            "SDXL": "low detail, distorted anatomy, unrealistic proportions, washed out colors, overexposed, watermark, text, bad hands, extra limbs, blurry background, chromatic aberration",
            "Flux": "chaotic composition, oversaturated colors, unnatural lighting, distorted proportions, messy textures, artifacts, watermark, text, cluttered scene, inconsistent perspective",
            "Flux Kontext": "chaotic composition, unnatural proportions, distorted lighting, artifacts, text, watermark, visual clutter, inconsistent perspective",
            "WAN 2.2": "lowres, bad anatomy, extra arms, extra legs, fused limbs, poorly drawn hands, incorrect eyes, distorted face, messy background, watermark, text, blurry, pixelated"
        }

        # Dynamically set negative_text based on model_type if not provided
        if not negative_text:
            model_negative_prompt = model_negative_presets.get(model_type, "")
            negative_text = model_negative_prompt

        # Validate API key is provided
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            raise ValueError("Google Gemini API key is missing or invalid. Please provide your API key.")

        # Generate a truly unique seed for this specific run

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
            
            # Add model_type-specific instructions
            model_type_instructions = {
                "SD1.5": """You are a prompt engineer for Stable Diffusion 1.5. 
                - Use a tag-based, keyword-heavy structure with comma-separated descriptors. 
                - Apply weighting syntax `(keyword:1.2)` where emphasis is needed.
                - Include 'magic words' like (masterpiece, best quality, ultra detailed) for higher quality.
                - Keep sentences short, focusing on strong descriptive tags.""",

                "SDXL": """You are a prompt engineer for Stable Diffusion XL. 
                - Use natural, flowing sentences with cinematic and photographic language.
                - Avoid overusing weighting syntax.
                - Focus on scene composition, realistic textures, and lighting.
                - Treat the prompt as an art direction or photography brief.""",

                "Flux": """You are a prompt engineer for the Flux model. 
                - Write prompts with narrative flow, multi-subject clarity, and contextual relationships.
                - Organize descriptions logically: environment → subject → details → mood.
                - Focus on scene composition, contextual relationships, and narrative flow.
                - Optionally use explicit 'Style:' and 'Mood:' sections to clarify tone.""",

                "Flux Kontext": """You are a prompt engineer for Flux Kontext. 
                - Focus on context-aware, narrative-driven, and conceptual prompts.
                - Expand descriptions into cinematic or storytelling language.
                - Use 'Style:' and 'Mood:' sections when appropriate for clarity.""",

                "WAN 2.2": """You are a prompt engineer for WAN 2.2. 
                - Use structured keyword chains with explicit style tokens (anime, digital art, etc.).
                - Keep prompts concise but rich in descriptors.
                - Optional light weighting `(keyword:1.2)` is acceptable.
                - Include style tokens when appropriate."""
            }

            model_type_prompt = model_type_instructions.get(model_type, "")
            
            # Create a prompt template instructing Gemini how to enhance the text
            conciseness_instruction = "Keep the prompt concise and under 50 words." if keep_concise else "Aim for around 50-100 words. Make it very descriptive."
            
            prompt_template = f"""
            {model_type_prompt}

            
            Your task is to enhance and elaborate the following prompt for optimal image generation:

            Original Prompt: {{user_prompt}}

            Your task: Enhance and elaborate the original prompt for optimal image generation.
            IMPORTANT: Your response MUST be a NEW and UNIQUE variation each time.
            IMPORTANT: Try to understand the essence of the prompt and expand upon it creatively. For example, if the base prompt is "an instagram selfie", do not return a painting style or a cartoon version. Instead, enhance the prompt with a unique setting, mood, or additional elements that would make it stand out.
            Create a completely different interpretation with:
            - Different artistic style than you would typically suggest, only if no style if given in the base prompt
            - Unique lighting conditions
            - Alternative composition approach
            - Varied details and elements
            - Understand if the user desires a particular style (Photorealistic, Cinematic, Anime, Painterly, Concept Art, Cyberpunk, etc.)
            - (Optional) Included technical details like the type of camera or lens used

            This is variation #{{seed}} in a batch generation process.
            
            {conciseness_instruction}
            Only output the enhanced prompt text, no explanations or commentary.
            Ignore any UNIQUENESS_MARKER tags in the prompt.
            """
            
            # Fill in the template with user's prompt and seed
            full_prompt = prompt_template.format(user_prompt=unique_text, seed=variation_seed)
            # Add extra uniqueness forcing parameters
            full_prompt += f"\n\nUnique variation #{variation_seed} @ {timestamp}. Make this absolutely distinct from all other variations."
            
            # Create generation config with temperature to increase variation
            generation_config = {
                "temperature": creativity,  # Use creativity value from input
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
        
        # Return both positive and negative conditioning, plus the seed used and enhanced text
        return ([[cond, {"pooled_output": pooled}]],
                [[neg_cond, {"pooled_output": neg_pooled}]],
                variation_seed,
                enhanced_prompt)
        
    # Add this property to tell ComfyUI to never cache the results of this node
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Tell ComfyUI this node always changes, preventing result caching.
        
        This forces ComfyUI to re-execute this node on each run, even in batched queue operations.
        """
        # Return current time to ensure the node is always considered "changed"
        return time.time()

from .metadata_embedder import EnhancedPromptMetadataEmbedder

# Register the node class for ComfyUI
NODE_CLASS_MAPPINGS = {
    "GoogleAIPromptEnhancer": GoogleAIPromptEnhancer,
    "EnhancedPromptMetadataEmbedder": EnhancedPromptMetadataEmbedder
}

# Define the display name for the node in ComfyUI interface
NODE_DISPLAY_NAME_MAPPINGS = {
    "GoogleAIPromptEnhancer": "Google AI Prompt Enhancer",
    "EnhancedPromptMetadataEmbedder": "Enhanced Prompt Metadata Embedder"
}