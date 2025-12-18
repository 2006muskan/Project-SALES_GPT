import google.generativeai as genai

# --- Configuration ---
# IMPORTANT: Replace "YOUR_API_KEY_HERE" with your actual Gemini API key.

try:
    api_key = "AIzaSyBpTrBSpRxQVleTj890smGcuXszPD0NzkA" # 👈 Paste your key here
    if api_key == "YOUR_API_KEY_HERE":
         print("🔴 API Key not provided. Please replace 'YOUR_API_KEY_HERE' with your actual key.")
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"Error configuring API: {e}")


# --- Model and Prompt Definition ---

# This is the "few-shot" prompt that teaches the model what to do.
# It includes instructions, data constraints, and examples for each category.
PROMPT_TEMPLATE = """
You are an expert in data classification. Your task is to classify user input into one of the following categories specified intents and extract relevant data:
1. Trend Analysis: Analyze trends in sales or revenue over time.
2. Comparative Analysis: Compare sales or revenue between different products or categories.
3. Outlier Analysis: Identify any outliers or anomalies in sales data.

Output should only contain the classified intent and any relevant extracted data in a specific format(comma-separated values):
if the output is Trend Analysis:
output format : Trend Analysis,start month,end month
Note: Months are [January, February, March, April, May, June, July, August, September, October, November, December]
if the output is Comparative Analysis:
output format : Comparative Analysis,product1,product2
Note: Products are [Laptop, Smartphone, Bed Sheet, Coffee Maker, Jeans, T-Shirt]
If the output is Outlier Analysis:
output format : Outlier Analysis,Category name
NOte: Categories are [Electronics, Home Goods, Apparel]
If the input does not match any of these categories
output format :Unrecognized Intent

Test_inputs:
Input:"Show me the revenue of spring season for Electronics?",
Output:"Trend Analysis,March,October"


Input:"Get me the outlier for apparel?",
Output:"Outlier Analysis,Apparel"

Input: {user_input}
Output:
"""

def classify_and_extract(user_input: str) -> str:
    """
    Classifies intent and extracts data from the input string using the Gemini API.

    Args:
        user_input: The text string from the user.

    Returns:
        A formatted string containing the intent and extracted data.
    """
    # Handle empty input gracefully
    if not user_input or not user_input.strip():
        return "Unrecognized Intent."

    # Configure the model for deterministic output
    generation_config = {"temperature": 0.1, "top_p": 1, "top_k": 1}
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=generation_config
    )

    # Format the full prompt with the user's input
    full_prompt = PROMPT_TEMPLATE.format(user_input=user_input)

    try:
        # Call the API
        response = model.generate_content(full_prompt)
        # Clean up and return the model's text response
        return response.text.strip()
    except Exception as e:
        return f"An error occurred with the API call: {e}"

# --- Example Usage ---
if __name__ == "__main__":
    print("🤖 Gemini Intent Classifier is ready. Type your requests below.\n")

    # Let's test with the provided samples and some new variations
    # test_inputs = [
    #     # Trend Analysis
    #     "How is the revenue from March to October",
    #     "Tell me how the sales this fall",
    #     "What was our performance like in the winter?",
    #     "Show sales in 1st Quarter",

    #     # Comparative Analysis
    #     "Compare the revenue between Laptop and SmartPhone.",
    #     "Which is greater sales Coffee Maker and SmartPhone.",
    #     "Contrast T-Shirt and Jeans revenue",

    #     # Outlier Analysis
    #     "When the sales are abnormally high or low for home goods.",
    #     "Tell me the outliers for Electronics",
    #     "Show me anomalies in Apparel sales",

    #     # Our qus
    #     "Show me the revenue of Autumn season for Electronics?",
    #     "During Diwali revenue of Electronics and Apparel.",

    #     # Unrecognized Intent
    #     "Hi , How are you?",
    #     "What is the capital of India?",
    #     "" # Empty string test
    # ]

    # for text in test_inputs:
    #     result = classify_and_extract(text)
    #     print(f"Input : \"{text}\"")
    #     print(f"Output: {result}\n" + "-"*40)