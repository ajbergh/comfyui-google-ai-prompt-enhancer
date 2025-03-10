# ComfyUI Google AI Prompt Enhancer

A ComfyUI extension that uses Google's Gemini AI to enhance and elaborate text prompts for image generation.

## Features

- Connects to Google's Gemini AI to transform simple prompts into detailed image generation instructions
- Seamlessly integrates with ComfyUI's workflow system
- Auto-resizing text input field
- Secure API key handling with masked display
- Error handling with graceful fallbacks

## Installation

### Using ComfyUI Manager (Recommended)
1. Install [ComfyUI Manager](https://github.com/ltdrdata/ComfyUI-Manager)
2. Search for "Google AI Prompt Enhancer" and install it
3. Required dependencies will be automatically installed

### Manual Installation
1. Clone this repository into your ComfyUI custom_nodes folder:
   ```
   git clone https://github.com/ajbergh/comfyui-google-ai-prompt-enhancer
   ```

2. Install the required Python packages:
   ```
   pip install google-generativeai
   ```

3. Restart ComfyUI

## Usage

1. Add the "Google AI Prompt Enhancer" node to your workflow
2. Enter your Google Gemini API key (it will be masked after entry for security)
3. Connect a CLIP model to the node
4. Enter your basic prompt
5. Connect the output to your image generation nodes

## Requirements

- Valid Google Gemini API key
- ComfyUI environment
- Python 3.8+

## License

MIT License - See LICENSE file for details