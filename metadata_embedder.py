import json

class EnhancedPromptMetadataEmbedder:
    """
    A node that adds the enhanced prompt to image metadata
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", ),
                "enhanced_prompt": ("STRING", {"multiline": True}),
                "original_prompt": ("STRING", {"multiline": True, "default": ""}),
                "negative_prompt": ("STRING", {"multiline": True, "default": ""}),
                "metadata": ("STRING", {"multiline": True, "default": "{}"})
            }
        }
        
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "metadata")
    FUNCTION = "embed_metadata"
    CATEGORY = "image/process"
    
    def embed_metadata(self, images, enhanced_prompt, original_prompt="", negative_prompt="", metadata="{}"):
        """
        Embeds the enhanced prompt into the image metadata
        """
        # Parse the existing metadata if any
        try:
            metadata_dict = json.loads(metadata)
        except:
            metadata_dict = {}
        
        # Add our enhanced prompt information
        metadata_dict["prompt"] = {
            "enhanced": enhanced_prompt,
            "original": original_prompt,
            "negative": negative_prompt
        }
        
        # Add Google AI Prompt Enhancer information
        if "google_ai_prompt_enhancer" not in metadata_dict:
            metadata_dict["google_ai_prompt_enhancer"] = {}
        
        metadata_dict["google_ai_prompt_enhancer"]["version"] = "1.0"
        
        # Convert back to JSON
        final_metadata = json.dumps(metadata_dict, indent=2)
        
        # Return the images with the enhanced metadata
        # The actual metadata embedding happens in the SaveImage node in ComfyUI
        return (images, final_metadata)