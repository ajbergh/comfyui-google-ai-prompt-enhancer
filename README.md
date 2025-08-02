# ComfyUI Google AI Prompt Enhancer

A ComfyUI extension that uses Google's Gemini AI to enhance and elaborate text prompts for image generation.

## Features

- **AI-Powered Prompt Enhancement:** Connects to Google's Gemini AI to transform simple prompts into detailed image generation instructions.
- **Model-Specific Optimization:** Use the `Model Type` dropdown (SD1.5, SDXL, Flux, etc.) to tailor the enhancement process for your target model.
- **Creativity Control:** Adjust the `Creativity` slider to control the randomness and artistic style of the enhanced prompt.
- **Conciseness Option:** A simple checkbox to generate shorter, more direct prompts.
- **Dynamic Negative Prompts:** Automatically populates a suggested negative prompt when you select a model type.
- **Seamless Integration:** Integrates directly into the ComfyUI workflow as a conditioning node.
- **Enhanced UX:**
    - Auto-resizing text input fields.
    - Secure API key handling with a show/hide toggle.
- **Metadata Embedding:** Includes a companion node to save the original and enhanced prompts to your image's metadata.
- **Error Handling:** Provides clear feedback and gracefully falls back to the original prompt on API errors.

## Installation

### Using ComfyUI Manager (Recommended)
1. Install [ComfyUI Manager](https://github.com/ltdrdata/ComfyUI-Manager)
2. Search for "Google AI Prompt Enhancer" and install it
3. Required dependencies will be automatically installed

### Manual Installation
1. Clone this repository into your ComfyUI `custom_nodes` folder:
   ```bash
   git clone https://github.com/ajbergh/comfyui-google-ai-prompt-enhancer
   ```

2. Install the required Python packages:
   ```bash
   pip install google-generativeai
   ```

3. Restart ComfyUI

## Usage

### Google AI Prompt Enhancer Node

1. Add the "Google AI Prompt Enhancer" node to your workflow (`Add Node` > `conditioning` > `Google AI Prompt Enhancer`).
2. Enter your Google Gemini API key. Use the `👁️` button to toggle visibility.
3. Connect a CLIP model to the `clip` input.
4. Enter your basic prompt in the `text` field.
5. Select the `model_type` that matches your target model (e.g., SDXL). The `negative_text` field will auto-populate.
6. Adjust the `Creativity` slider to influence how much the AI varies the prompt. Higher values are more creative.
7. Check `keep_concise` if you prefer a shorter prompt.
8. Connect the `positive` and `negative` outputs to your KSampler node.

### Enhanced Prompt Metadata Embedder Node

The Enhanced Prompt Metadata Embedder allows you to store your original and enhanced prompts directly in the image metadata:

1. Add the "Enhanced Prompt Metadata Embedder" node to your workflow.
2. Connect your images to the `images` input.
3. Connect the `enhanced_prompt` (string) output from the enhancer node.
4. Optionally provide the original and negative prompts.
5. Connect the `IMAGES` output to a SaveImage node to save the images with embedded metadata.

## Workflow Example

A basic workflow might look like:
1. CLIP Text Encoder → Google AI Prompt Enhancer
2. KSampler (with Google AI Prompt Enhancer connected)
3. VAE Decoder (from KSampler)
4. Enhanced Prompt Metadata Embedder (with VAE output and prompt data)
5. SaveImage

## Requirements

- Valid Google Gemini API key
- ComfyUI environment
- Python 3.8+

## License

MIT License - See LICENSE file for details