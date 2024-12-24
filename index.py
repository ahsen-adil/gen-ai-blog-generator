import os
import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import speech_recognition as sr
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the API key
api_key = os.getenv("API_KEY")
if not api_key:
    st.error("API_KEY is not set. Please add it to your environment or .env file.")
    st.stop()

genai.configure(api_key=api_key)

# Function to upload a file to Gemini
def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini."""
    file = genai.upload_file(path, mime_type=mime_type)
    return file

# Function to capture voice input and convert it to text
def get_speech_input():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        st.write("Listening for your question... (Speak now!)")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        # Convert speech to text
        query = recognizer.recognize_google(audio)
        st.write(f"You said: {query}")
        return query
    except sr.UnknownValueError:
        st.error("Sorry, I could not understand that.")
        return None
    except sr.RequestError:
        st.error("Could not request results from Google Speech Recognition service.")
        return None

# Streamlit UI
st.title("Gemini AI Blog Post Generator with Voice")
st.write("Generate an engaging blog post using AI by providing a prompt. Optionally, upload an image to enhance the result. Get the response in both text and audio!")

# File upload section (optional for images)
uploaded_file = st.file_uploader("Upload an image (optional, e.g., JPEG, PNG)", type=["jpeg", "png"])

# Voice input button
if st.button("Use Voice Input"):
    user_prompt = get_speech_input()
    if user_prompt:
        st.session_state.user_prompt = user_prompt

# Text area input for a fallback option
if 'user_prompt' not in st.session_state:
    st.session_state.user_prompt = ""

if not st.session_state.user_prompt:
    st.session_state.user_prompt = st.text_area("Enter your prompt", placeholder="Describe what you want the AI to generate.")

# Ensure the user has provided a prompt before generating
if st.button("Generate"):
    if not st.session_state.user_prompt or st.session_state.user_prompt.strip() == "":
        st.error("Please enter a prompt or use voice input.")
    else:
        try:
            # If an image is uploaded, process it
            if uploaded_file is not None:
                # Save uploaded file locally
                temp_file_path = f"temp_{uploaded_file.name}"
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Upload the file to Gemini
                uploaded_gemini_file = upload_to_gemini(temp_file_path, mime_type="image/jpeg")
                st.success(f"File uploaded successfully: {uploaded_gemini_file.uri}")
            else:
                uploaded_gemini_file = None  # No image provided

            # Create the model for content generation
            generation_config = {
                "temperature": 0.9,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            }

            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
            )

            # Start the chat session using the prompt (and image if provided)
            chat_history = [{
                "role": "user",
                "parts": [st.session_state.user_prompt],
            }]
            if uploaded_gemini_file:
                chat_history[0]["parts"].insert(0, uploaded_gemini_file)

            chat_session = model.start_chat(history=chat_history)

            # Generate response
            response = chat_session.send_message("Generate content")
            response_text = response.text

            st.subheader("Generated Blog Post")
            st.write(response_text)

            # Convert response to audio
            tts = gTTS(text=response_text, lang='en')
            audio_path = "response_audio.mp3"
            tts.save(audio_path)

            # Display audio player
            st.subheader("Listen to the Response")
            st.audio(audio_path, format="audio/mp3")

        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            # Clean up the temporary file
            if uploaded_file is not None and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
