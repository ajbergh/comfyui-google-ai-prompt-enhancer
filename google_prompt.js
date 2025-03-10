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

                // Find and customize the prompt text input widget
                const textBoxWidget = this.widgets.find((w) => w.name === "text");
                textBoxWidget.inputEl.placeholder = "Enter your prompt here";

                // Implement auto-resizing functionality for the text box
                const onInput = textBoxWidget.callback;
                textBoxWidget.callback = function () {
                    // Call the original callback first
                    onInput?.apply(this, arguments);
                    
                    // Auto-resize logic - temporarily set height to 0 to calculate proper scrollHeight
                    this.inputEl.style.height = 0;
                    this.inputEl.style.height = `${this.inputEl.scrollHeight}px`;
                    
                    // Tell ComfyUI to redraw the canvas with updated node dimensions
                    app.graph.setDirtyCanvas(true);
                }
                
                // Trigger the callback once to initialize the sizing
                textBoxWidget.callback();

                return r;
            };
        }
    },
});