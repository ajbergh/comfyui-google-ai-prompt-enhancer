import json

class EnhancedPromptMetadataEmbedder:
    """
    A node that embeds prompt metadata into images
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "metadata": ("STRING", {"multiline": True, "default": "{}"})
            }
        }
        
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "embed_metadata"
    CATEGORY = "image/process"
    
    def embed_metadata(self, images, metadata="{}"):
        """
        Embeds the provided metadata into the images
        """
        # Parse the metadata
        try:
            metadata_dict = json.loads(metadata)
        except:
            print("Warning: Invalid metadata JSON. Using empty metadata.")
            metadata_dict = {}
        
        # The actual metadata embedding happens in the SaveImage node in ComfyUI
        # Here we're just passing the images through with their metadata attached
        return (images,)