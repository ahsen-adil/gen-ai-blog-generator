import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the generative AI model
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Streamlit UI
st.title("AI Content Generator")
st.write("Enter a prompt below and see the generated response!")

# User input
user_input = st.text_input("Enter your prompt here:", placeholder="Type something...")

if st.button("Generate Response"):
    if user_input:
        with st.spinner("Generating response..."):
            try:
                response = model.generate_content(user_input)
                st.success("Response generated successfully!")
                st.text_area("Generated Response:", value=response.text, height=200)
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please enter a prompt before generating a response.")
