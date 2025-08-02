/**
 * Google AI Prompt Enhancer - ComfyUI Frontend Extension
 * =====================================================
 * 
 * This extension enhances the UI for the Google AI Prompt Enhancer node in ComfyUI.
 * It customizes the appearance and behavior of input widgets to improve user experience.
 * 
 * Features:
 * - Custom placeholders for API key and prompt input fields
 * - Auto-resizing text area for prompt input
 * - Improved visual feedback
 * 
 * Author: Adam Bergh
 * License: MIT
 */

import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "Comfy.GooglePrompt",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // Only modify our specific node type
        if (nodeData.name === "GoogleAIPromptEnhancer") {
            // Store the original onNodeCreated function
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            
            // Override the onNodeCreated function with our custom implementation
            nodeType.prototype.onNodeCreated = function () {
                // Call the original implementation first
                const r = onNodeCreated?.apply(this, arguments);

                // Find and customize the API key input widget
                const apiWidget = this.widgets.find((w) => w.name === "api_key");
                if (apiWidget) {
                    // Set placeholder and ensure it's a password field initially
                    apiWidget.inputEl.placeholder = "Enter your Google Gemini API Key Here";
                    apiWidget.inputEl.type = "password";
                    // Ensure the widget's type property is also set for consistency
                    apiWidget.type = "password";

                    // Create a toggle button for showing/hiding the password
                    const toggleBtn = document.createElement("button");
                    toggleBtn.textContent = "👁️";
                    toggleBtn.style.marginLeft = "5px";
                    toggleBtn.style.padding = "2px 5px";
                    toggleBtn.style.cursor = "pointer";
                    toggleBtn.title = "Show/Hide API Key";
                    toggleBtn.onclick = (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        const isPassword = apiWidget.inputEl.type === "password";
                        apiWidget.inputEl.type = isPassword ? "text" : "password";
                        apiWidget.type = apiWidget.inputEl.type;
                        toggleBtn.textContent = isPassword ? "🔒" : "👁️";
                    };

                    // Insert the toggle button after the input element
                    apiWidget.inputEl.parentNode.insertBefore(toggleBtn, apiWidget.inputEl.nextSibling);
                }

                // Find and customize the model dropdown widget
                const modelWidget = this.widgets.find((w) => w.name === "model");
                if (modelWidget) {
                    // Add a title attribute for additional information on hover
                    modelWidget.inputEl.title = "Select which Google Gemini model to use for prompt enhancement";
                    
                    // Apply some custom styling to make the dropdown more visible
                    modelWidget.inputEl.style.width = "100%";
                    modelWidget.inputEl.style.padding = "4px";
                    modelWidget.inputEl.style.borderRadius = "4px";
                }

                // Find and customize the model_type dropdown widget
                const modelTypeWidget = this.widgets.find((w) => w.name === "model_type");
                const negativeTextWidget = this.widgets.find((w) => w.name === "negative_text");

                if (modelTypeWidget && negativeTextWidget) {
                    modelTypeWidget.inputEl.title =
                        "Select the type of Stable Diffusion model. This influences how the prompt is enhanced for optimal results.";
                    modelTypeWidget.inputEl.style.width = "100%";
                    modelTypeWidget.inputEl.style.padding = "4px";
                    modelTypeWidget.inputEl.style.borderRadius = "4px";

                    const modelNegativePresets = {
                        "SD1.5": "blurry, lowres, bad anatomy, extra limbs, poorly drawn hands, fused fingers, mutated hands, deformed face, long neck, watermark, text, logo, grainy, jpeg artifacts",
                        "SDXL": "low detail, distorted anatomy, unrealistic proportions, washed out colors, overexposed, watermark, text, bad hands, extra limbs, blurry background, chromatic aberration",
                        "Flux": "chaotic composition, oversaturated colors, unnatural lighting, distorted proportions, messy textures, artifacts, watermark, text, cluttered scene, inconsistent perspective",
                        "Flux Kontext": "chaotic composition, unnatural proportions, distorted lighting, artifacts, text, watermark, visual clutter, inconsistent perspective",
                        "WAN 2.2": "lowres, bad anatomy, extra arms, extra legs, fused limbs, poorly drawn hands, incorrect eyes, distorted face, messy background, watermark, text, blurry, pixelated"
                    };

                    // Store the original callback to be called later
                    const originalCallback = modelTypeWidget.callback;

                    // Define the new callback function
                    modelTypeWidget.callback = (v) => {
                        // Check if the current negative prompt is one of the preset values.
                        const currentNegative = negativeTextWidget.value.trim();
                        const isAPreset = Object.values(modelNegativePresets).includes(currentNegative);

                        // Only update the negative prompt if it's empty or if it's one of our presets.
                        // This prevents overwriting a user's custom negative prompt.
                        if (!currentNegative || isAPreset) {
                            negativeTextWidget.value = modelNegativePresets[v] || "";
                            
                            // Manually trigger the input event for the text area to update its size
                            if (negativeTextWidget.inputEl) {
                                negativeTextWidget.inputEl.dispatchEvent(new Event('input', { bubbles: true }));
                            }
                        }
                        
                        // Call the original callback if it exists
                        if (originalCallback) {
                            return originalCallback.apply(this, arguments);
                        }
                    };

                    // Trigger the callback once on node creation to set the initial value based on the default model type.
                    setTimeout(() => {
                        if (modelTypeWidget.value) {
                            modelTypeWidget.callback(modelTypeWidget.value);
                        }
                    }, 0);
                }

                // Find and customize the seed override widget
                const seedWidget = this.widgets.find((w) => w.name === "seed_override");
                if (seedWidget) {
                    seedWidget.inputEl.title = "Set to 0 for random unique prompts in each queue run, or set specific value for reproducible results";
                    
                    // Add a helpful tooltip via the label
                    const originalLabel = seedWidget.label;
                    seedWidget.label = "Seed (0 = random unique)";
                }

                // Find and customize the prompt text input widget
                const textBoxWidget = this.widgets.find((w) => w.name === "text");
                textBoxWidget.inputEl.placeholder = "Enter your prompt here";

                // Find and customize the negative prompt text input widget
                negativeTextWidget.inputEl.placeholder = "Enter negative prompt here (not enhanced by AI)";
                
                // Apply some styling to differentiate it from the positive prompt
                negativeTextWidget.inputEl.style.borderColor = "#ff6b6b";
                negativeTextWidget.inputEl.style.backgroundColor = "rgba(255, 107, 107, 0.05)";

                // Implement auto-resizing functionality for both text boxes
                const setupAutoResize = (widget) => {
                    const onInput = () => {
                        // Auto-resize logic - temporarily set height to 0 to calculate proper scrollHeight
                        widget.inputEl.style.height = 'auto';
                        widget.inputEl.style.height = `${widget.inputEl.scrollHeight}px`;
                        
                        // Tell ComfyUI to redraw the canvas with updated node dimensions
                        app.graph.setDirtyCanvas(true);
                    };
                    
                    widget.inputEl.addEventListener('input', onInput);
                    
                    // Trigger the resize once to initialize the sizing
                    setTimeout(() => onInput(), 0);
                };
                
                setupAutoResize(textBoxWidget);
                setupAutoResize(negativeTextWidget);

                return r;
            };
        }
    },
});