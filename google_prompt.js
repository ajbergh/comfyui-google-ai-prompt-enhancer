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
                apiWidget.inputEl.placeholder = "Enter your Google Gemini API Key Here";

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

                // Find and customize the prompt text input widget
                const textBoxWidget = this.widgets.find((w) => w.name === "text");
                textBoxWidget.inputEl.placeholder = "Enter your prompt here";

                // Find and customize the negative prompt text input widget
                const negativeTextWidget = this.widgets.find((w) => w.name === "negative_text");
                negativeTextWidget.inputEl.placeholder = "Enter negative prompt here (not enhanced by AI)";
                
                // Apply some styling to differentiate it from the positive prompt
                negativeTextWidget.inputEl.style.borderColor = "#ff6b6b";
                negativeTextWidget.inputEl.style.backgroundColor = "rgba(255, 107, 107, 0.05)";

                // Implement auto-resizing functionality for both text boxes
                const setupAutoResize = (widget) => {
                    const onInput = widget.callback;
                    widget.callback = function () {
                        // Call the original callback first
                        onInput?.apply(this, arguments);
                        
                        // Auto-resize logic - temporarily set height to 0 to calculate proper scrollHeight
                        this.inputEl.style.height = 0;
                        this.inputEl.style.height = `${this.inputEl.scrollHeight}px`;
                        
                        // Tell ComfyUI to redraw the canvas with updated node dimensions
                        app.graph.setDirtyCanvas(true);
                    }
                    
                    // Trigger the callback once to initialize the sizing
                    widget.callback();
                };
                
                setupAutoResize(textBoxWidget);
                setupAutoResize(negativeTextWidget);

                return r;
            };
        }
    },
});