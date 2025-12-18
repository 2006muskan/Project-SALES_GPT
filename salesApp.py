import streamlit as st
import pandas as pd
import json

import os
from PIL import Image
from Checking import clean_transaction_data
from Checking import DataProcessing
from Checking import IntentIdentifier
import google.generativeai as genai

with st.form(key="sample_form"):
   #title
   st.markdown(""" <h1 style='text-align: center; color: #000000;'>Sales GPT</h1> """, unsafe_allow_html=True)
   #logo
   st.image(os.path.join(os.getcwd(),"static","Arjuna.jpg"),width=200)
   #input
   user_input = st.text_input("PROMPT")

   #outputs
   #upload file   
   uploaded_file=st.file_uploader("Upload a CSV ,Excel,", type=['csv','xlsx'])
   #if uploaded_file is not None:
   if uploaded_file:
      if uploaded_file.name.endswith(".csv"):
         df=pd.read_csv(uploaded_file)
         st.write("CSV Preview")
         st.dataframe(df.head())
         output_csv_file = 'cleaned_data.csv'
         df = clean_transaction_data(df, output_file=output_csv_file)
         extractedData = IntentIdentifier.classify_and_extract(user_input)
         refinedPrompt = DataProcessing(extractedData,df,user_input)
         if(refinedPrompt == "Unknown intent"):
            output = (
               "Sorry, I cannot process this request. Please try again with a Following Prompt as an example\n"
               "1. Compare the Revenue of Laptop and Phone.\n"
               "2. Tell me the outlier of Apparel\n"
               "3. How are sales in 1st quarter"
            )
         else:
            model = genai.GenerativeModel(model_name="gemini-2.5-flash")
            output = model.generate_content(refinedPrompt).text.strip() 

      elif uploaded_file.name.endswith(".xlsx"):
         df=pd.read_excel(uploaded_file)
         st.write("Excel Preview")
         st.dataframe(df.head())
   
   if user_input:
      st.subheader("REPORT")
      st.write(output)

   
   submit_button = st.form_submit_button("Submit")

   if submit_button:
   # st.form_submit_button()
      #st.form_submit_button(label="submit")
      st.success("File uploaded successfully!")


# Custom CSS for background color
page_bg_color = """
<style>
[data-testid="stAppViewContainer"] {
    background-color: #F3E5F5; /* Light Khaki color */
}

# [data-testid="stHeader"] {
#      background-color: rgba(32, 178, 170, 0.8); /* Light Sea Green with transparency */
}
</style>
"""

# Apply the custom style
st.markdown(page_bg_color, unsafe_allow_html=True)