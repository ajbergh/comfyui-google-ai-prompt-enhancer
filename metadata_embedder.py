import json
import comfy.sd

class PromptMetadataEmbedder:
    """
    A node that prepares prompt and workflow metadata to be embedded into images by the SaveImage node.
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "positive_prompt": ("STRING", {"multiline": True, "default": ""}),
            },
            "hidden": {
                "prompt": "PROMPT", 
                "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }
        
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("positive_prompt_text",)
    FUNCTION = "embed_metadata"
    OUTPUT_NODE = True
    CATEGORY = "Google AI"
    
    def embed_metadata(self, positive_prompt, prompt=None, extra_pnginfo=None):
        """
        Adds the positive prompt and the workflow to the extra_pnginfo dictionary.
        """
        # The core ComfyUI SaveImage node handles the actual embedding.
        # We just need to prepare the data for it.
        
        if prompt is None or extra_pnginfo is None:
            # This node is not connected to a workflow, so we can't embed metadata.
            # We will just return the prompt text.
            return (positive_prompt,)

        # Add the positive prompt to the workflow data
        # The SaveImage node will use the 'prompt' field from extra_pnginfo for the 'Description' PNG chunk
        workflow_metadata = {
            "prompt": prompt,
            "extra_pnginfo": extra_pnginfo
        }
        
        # We find the KSampler node (or a similar one) to inject our positive prompt into the workflow metadata
        # This makes it visible in the UI when loading the image
        for node_id, node_data in workflow_metadata["prompt"].items():
            if "inputs" in node_data and "positive" in node_data["inputs"]:
                # Found a node with a 'positive' input, let's update it.
                # This is a bit of a heuristic, but it covers common samplers.
                node_data["inputs"]["positive"] = positive_prompt
                break # Stop after finding the first one

        # The SaveImage node reads from the 'extra_pnginfo' dictionary.
        # We add our workflow and prompt information here.
        extra_pnginfo["workflow"] = json.dumps(workflow_metadata["prompt"], indent=2)
        extra_pnginfo["prompt"] = json.dumps({"positive_prompt": positive_prompt}, indent=2)

        return {"ui": {"text": "Workflow and prompt metadata will be embedded."}, "result": (positive_prompt,)}