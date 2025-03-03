import streamlit as st
import base64
import json
import re
import pandas as pd
from pathlib import Path
from together import Together
from dotenv import load_dotenv
import os
import datetime
import speech_recognition as sr
from gtts import gTTS
import tempfile
import io
import threading
import time

# Load environment variables
load_dotenv()

# User authentication system
USER_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

def authenticate_user(username, password):
    users = load_users()
    return users.get(username) == password

def register_user(username, password):
    users = load_users()
    if username in users:
        return False  # User already exists
    users[username] = password
    save_users(users)
    return True

def login_page():
    st.title("🔐 Login to Medical Image Analysis")
    choice = st.radio("Select an option", ["Login", "Register"])
    
    if choice == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.button("Login")
        
        if login_button:
            if authenticate_user(username, password):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("Invalid username or password")
    else:
        username = st.text_input("Choose a username")
        password = st.text_input("Choose a password", type="password")
        register_button = st.button("Register")
        
        if register_button:
            if register_user(username, password):
                st.success("Registration successful! You can now log in.")
            else:
                st.error("Username already exists. Choose a different one.")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login_page()
    st.stop()

# Add custom CSS loader
def load_css():
    with open('styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Create directories for storing JSON files if they don't exist
def create_storage_directories():
    os.makedirs("data/prescriptions", exist_ok=True)
    os.makedirs("data/diagnostics", exist_ok=True)
    os.makedirs("data/voice_conversations", exist_ok=True)
    return "data/prescriptions", "data/diagnostics", "data/voice_conversations"

# Save JSON data to file
def save_json_data(data, directory, file_prefix):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{file_prefix}_{timestamp}.json"
    filepath = os.path.join(directory, filename)
    
    with open(filepath, 'w') as f:
        json.dump(data, indent=4, fp=f)
    
    return filepath

# Voice Assistant Class
class VoiceAssistant:
    def __init__(self, llm_client):
        self.recognizer = sr.Recognizer()
        self.llm_client = llm_client
        self.conversation_history = []
        
    def listen(self):
        with sr.Microphone() as source:
            st.info("Listening... Speak now.")
            self.recognizer.adjust_for_ambient_noise(source)
            try:
                audio = self.recognizer.listen(source, timeout=5)
                st.info("Processing your speech...")
                return audio
            except sr.WaitTimeoutError:
                st.warning("No speech detected. Please try again.")
                return None
            except Exception as e:
                st.error(f"Error capturing audio: {str(e)}")
                return None
    
    def transcribe(self, audio):
        try:
            text = self.recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            st.warning("Could not understand audio. Please try again.")
            return None
        except sr.RequestError:
            st.error("Could not request results from speech recognition service.")
            return None
        except Exception as e:
            st.error(f"Error in speech recognition: {str(e)}")
            return None
    
    def process_query(self, query, context=None):
        # Add the user query to conversation history
        self.conversation_history.append({"role": "user", "content": query})
        
        try:
            # Construct prompt with conversation history for context and request for brevity
            system_message = "Please provide brief and concise responses suitable for voice output. Limit to 2-3 short sentences when possible."
            
            messages = [{"role": "system", "content": system_message}]
            
            # Add recent conversation history (up to last 6 messages)
            recent_history = self.conversation_history[-6:] if len(self.conversation_history) > 6 else self.conversation_history
            for msg in recent_history:
                messages.append({"role": msg["role"], "content": msg["content"]})
            
            # If there's context (e.g., from image analysis), add it
            if context:
                context_message = f"Based on the analysis results: {json.dumps(context, indent=2)}, please provide a concise response to: {query}"
                messages.append({"role": "system", "content": context_message})
                
            # Add final instruction for brevity
            messages.append({"role": "system", "content": "Remember to keep your response brief and concise for voice output. Focus only on the most important information."})
            
            response = self.llm_client.chat.completions.create(
                model="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
                messages=messages,
                stream=False
            )
            
            response_text = response.choices[0].message.content
            
            # Store full response in conversation history
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            # Create a concise version for voice output
            concise_response = self.generate_concise_response(response_text, query, context)
            
            return {"full": response_text, "concise": concise_response}
        
        except Exception as e:
            st.error(f"Error processing query with LLM: {str(e)}")
            error_msg = "Sorry, I encountered an error while processing your query."
            return {"full": error_msg, "concise": error_msg}
    
    def generate_concise_response(self, full_response, query, context=None):
        """Generate a concise version of the response for voice output"""
        try:
            summarize_messages = [
                {"role": "system", "content": "You are a summarizer that creates very brief summaries for voice output."},
                {"role": "user", "content": f"Summarize the following in 1-2 simple sentences for voice output:\n\n{full_response}"}
            ]
            
            summary_response = self.llm_client.chat.completions.create(
                model="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
                messages=summarize_messages,
                stream=False
            )
            
            concise_text = summary_response.choices[0].message.content
            
            # Ensure it's not too long (roughly 30 words max for voice)
            words = concise_text.split()
            if len(words) > 30:
                concise_text = ' '.join(words[:30]) + "..."
                
            return concise_text
            
        except Exception as e:
            st.warning(f"Error creating concise response: {str(e)}")
            # Fall back to first 2 sentences of the full response
            sentences = full_response.split('.')[:2]
            return '. '.join(sentences) + '.'
    
    def speak(self, text):
        try:
            # Create a temporary file for the TTS audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio:
                st.info(f"Converting to speech: '{text}'")
                
                # Convert text to speech and save to temporary file
                tts = gTTS(text=text, lang='en', slow=False)
                tts.save(temp_audio.name)
                
                # Read the audio bytes
                with open(temp_audio.name, 'rb') as audio_file:
                    audio_bytes = audio_file.read()
                
                # Encode audio bytes to Base64
                audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
                
                # Embed an HTML audio element with autoplay
                audio_html = f"""
                <audio autoplay>
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    Your browser does not support the audio element.
                </audio>
                """
                st.markdown(audio_html, unsafe_allow_html=True)
            
            # Clean up temp file after a short delay in a background thread
            def cleanup_temp_file(filename, delay=5):
                time.sleep(delay)
                try:
                    if os.path.exists(filename):
                        os.unlink(filename)
                except Exception as e:
                    st.warning(f"Cleanup warning: {str(e)}")
                    
            cleanup_thread = threading.Thread(target=cleanup_temp_file, args=(temp_audio.name,))
            cleanup_thread.daemon = True
            cleanup_thread.start()
            
            return True
            
        except Exception as e:
            st.error(f"Error in text-to-speech: {str(e)}")
            return False
    
    def save_conversation(self, directory):
        if not self.conversation_history:
            return None
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"voice_conversation_{timestamp}.json"
        filepath = os.path.join(directory, filename)
        
        with open(filepath, 'w') as f:
            json.dump(self.conversation_history, f, indent=4)
        
        return filepath

class ImageAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            st.error("API key not found. Please check your .env file.")
            return
        self.client = Together(api_key=self.api_key)
        
    def encode_image(self, image_file):
        try:
            return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            st.error(f"Error encoding image: {str(e)}")
            return None

    def analyze_prescription(self, image_file):
        prompt = """You are a highly accurate AI specialized in extracting structured information from medical prescriptions.  
Your task is to analyze the provided prescription image and return the details in the following strict JSON format:  

{  
    "Date": "<Extracted Date>",  
    "Patient": {  
        "Name": "<Extracted Name>",  
        "Age": "<Extracted Age>"  
    },  
    "Medicines": [  
        {  
            "Type": "<Tablet/Capsule/Syrup/etc.>",  
            "Medicine": "<Medicine Name>",  
            "Dosage": "<Dosage Instructions>",  
            "Timings": [<If `X` is 1, replace it with a morning time (e.g., 8 AM, 9 AM, etc.)>, <If `Y` is 1, replace it with an afternoon time (e.g., 1 PM, 2 PM, etc.)>, <If `Z` is 1, replace it with a night/evening time (e.g., 7 PM, 8 PM, etc.).>]  
        }  
    ]  
}  

Timings Extraction Rules:  
- If the dosage format is in "X-Y-Z" (e.g., "1-0-1"):  
  - If `X` is 1, replace it with a morning time (e.g., 8 AM, 9 AM, etc.).  
  - If `Y` is 1, replace it with an afternoon time (e.g., 1 PM, 2 PM, etc.).  
  - If `Z` is 1, replace it with a night/evening time (e.g., 7 PM, 8 PM, etc.).  
  - If any of these are 0, do not include a time for that slot.  
- Ensure "Timings" always contains integers only.  
Return only the JSON output, without additional text or explanations."""
        
        base64_image = self.encode_image(image_file)
        if not base64_image:
            return None

        try:
            response = self.client.chat.completions.create(
                model="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                        ],
                    }
                ],
                stream=False
            )

            full_response = response.choices[0].message.content
            json_match = re.search(r"\{.*\}", full_response, re.DOTALL)
            if json_match:
                extracted_data = json.loads(json_match.group(0))
                return extracted_data
            return None

        except Exception as e:
            st.error(f"Error analyzing prescription: {str(e)}")
            return None

    def analyze_diagnostic_image(self, image_file):
        prompt = """Analyze the provided medical image and provide analysis in this JSON format:
        {
            "Predicted_Disease": "<Predict accurate name of the Disease/Condition Name>",
            "Confidence_Score": "<AI Confidence Level (0-100%)>",
            "Description": "<Brief explanation of the disease>",
            "Possible_Causes": ["<Cause 1>", "<Cause 2>", "<Cause 3>"],
            "Recommended_Actions": ["<Action 1>", "<Action 2>", "<Action 3>"]
        }
        Ensure the response is accurate and useful for a medical specialist. If the image is unclear, specify that in the Description field."""
        
        base64_image = self.encode_image(image_file)
        if not base64_image:
            return None

        try:
            response = self.client.chat.completions.create(
                model="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                        ],
                    }
                ],
                stream=False
            )

            full_response = response.choices[0].message.content
            json_match = re.search(r"\{.*\}", full_response, re.DOTALL)
            if json_match:
                extracted_data = json.loads(json_match.group(0))
                return extracted_data
            return None

        except Exception as e:
            st.error(f"Error analyzing diagnostic image: {str(e)}")
            return None

def main():
    st.set_page_config(
        page_title="Medical Image Analysis",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load custom CSS
    load_css()
    
    # Create storage directories
    prescriptions_dir, diagnostics_dir, voice_dir = create_storage_directories()
    
    # Custom styled header
    st.markdown("""
        <div class="main-header">
            <h1>🏥 Medical Image Analysis System</h1>
            <p class="subtitle">AI-Powered Medical Image Analysis</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("""
        <div class="sidebar-header">
            <h3>Navigation</h3>
        </div>
    """, unsafe_allow_html=True)
    
    page = st.sidebar.radio("", ["Prescription Analysis", "Diagnostic Image Analysis", "Voice Assistant"])
    
    analyzer = ImageAnalyzer()
    
    # Initialize Voice Assistant
    if "voice_assistant" not in st.session_state:
        st.session_state.voice_assistant = VoiceAssistant(analyzer.client)
    
    # Initialize analysis results for context in voice assistant
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None
        
    # Initialize text input state for the voice assistant
    if "show_text_input" not in st.session_state:
        st.session_state.show_text_input = False

    if page == "Prescription Analysis":
        st.markdown('<div class="section-header">', unsafe_allow_html=True)
        st.title("Prescription Analysis")
        st.write("Upload a prescription image to extract details")
        st.markdown('</div>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Choose a prescription image", type=["jpg", "jpeg", "png"])
        
        if uploaded_file:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="image-container">', unsafe_allow_html=True)
                st.image(uploaded_file, use_container_width=True, caption="Uploaded Prescription")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                if st.button("🔍 Analyze Prescription", type="primary"):
                    with st.spinner("🔄 Processing prescription..."):
                        results = analyzer.analyze_prescription(uploaded_file)
                        
                        if results:
                            # Save the JSON data
                            saved_path = save_json_data(results, prescriptions_dir, "prescription")
                            
                            # Store results for voice assistant context
                            st.session_state.analysis_results = results
                            
                            st.success(f"✅ Analysis Complete! Data saved to {saved_path}")
                            
                            st.markdown('<div class="results-card">', unsafe_allow_html=True)
                            st.subheader("Patient Information")
                            st.write(f"Name: {results.get('Patient', {}).get('Name', 'N/A')}")
                            st.write(f"Age: {results.get('Patient', {}).get('Age', 'N/A')}")
                            st.write(f"Date: {results.get('Date', 'N/A')}")
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            if results.get('Medicines'):
                                st.markdown('<div class="results-card">', unsafe_allow_html=True)
                                st.subheader("Prescribed Medicines")
                                df = pd.DataFrame(results['Medicines'])
                                st.table(df)
                                st.markdown('</div>', unsafe_allow_html=True)
                        else:
                            st.error("❌ Analysis failed. Please try again with a clearer image.")

    elif page == "Diagnostic Image Analysis":
        st.markdown('<div class="section-header">', unsafe_allow_html=True)
        st.title("Diagnostic Image Analysis")
        st.write("Upload a diagnostic image for detailed analysis")
        st.markdown('</div>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Choose a diagnostic image", type=["jpg", "jpeg", "png"])
        
        if uploaded_file:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="image-container">', unsafe_allow_html=True)
                st.image(uploaded_file, use_container_width=True, caption="Uploaded Diagnostic Image")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                if st.button("🔬 Analyze Image", type="primary"):
                    with st.spinner("🔄 Analyzing image..."):
                        results = analyzer.analyze_diagnostic_image(uploaded_file)
                        
                        if results:
                            # Save the JSON data
                            saved_path = save_json_data(results, diagnostics_dir, "diagnostic")
                            
                            # Store results for voice assistant context
                            st.session_state.analysis_results = results
                            
                            st.success(f"✅ Analysis Complete! Data saved to {saved_path}")
                            
                            st.markdown('<div class="results-card">', unsafe_allow_html=True)
                            st.subheader("Disease Prediction")
                            st.write(f"Predicted Disease: {results.get('Predicted_Disease', 'N/A')}")
                            st.write(f"Confidence Score: {results.get('Confidence_Score', 'N/A')}")
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown('<div class="results-card">', unsafe_allow_html=True)
                            st.subheader("Description")
                            st.write(results.get('Description', 'N/A'))
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown('<div class="results-card">', unsafe_allow_html=True)
                            st.subheader("Possible Causes")
                            for cause in results.get('Possible_Causes', []):
                                st.write(f"• {cause}")
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown('<div class="results-card">', unsafe_allow_html=True)
                            st.subheader("Recommended Actions")
                            for action in results.get('Recommended_Actions', []):
                                st.write(f"• {action}")
                            st.markdown('</div>', unsafe_allow_html=True)
                        else:
                            st.error("❌ Analysis failed. Please try again with a clearer image.")
    
    else:  # Voice Assistant Page
        st.markdown('<div class="section-header">', unsafe_allow_html=True)
        st.title("Medical Voice Assistant")
        st.write("Interact with the AI using your voice or text")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display conversation history
        st.markdown('<div class="conversation-container">', unsafe_allow_html=True)
        st.subheader("Conversation History")
        
        for message in st.session_state.voice_assistant.conversation_history:
            if message["role"] == "user":
                st.markdown(f'<div class="user-message">👤 You: {message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="assistant-message">🤖 Assistant: {message["content"]}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Voice control options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎤 Start Voice Input", type="primary"):
                audio = st.session_state.voice_assistant.listen()
                if audio:
                    transcribed_text = st.session_state.voice_assistant.transcribe(audio)
                    if transcribed_text:
                        st.info(f"You said: {transcribed_text}")
                        # Process query and store response for display
                        response = st.session_state.voice_assistant.process_query(
                            transcribed_text, 
                            context=st.session_state.analysis_results
                        )
                        st.session_state.last_response = response
                        st.session_state.last_input_method = "voice"
                        st.rerun()
        
        with col2:
            if st.button("📝 Text Input"):
                st.session_state.show_text_input = not st.session_state.show_text_input
                st.rerun()
        
        with col3:
            if st.button("💾 Save Conversation"):
                if st.session_state.voice_assistant.conversation_history:
                    saved_path = st.session_state.voice_assistant.save_conversation(voice_dir)
                    if saved_path:
                        st.success(f"Conversation saved to {saved_path}")
                    else:
                        st.warning("Nothing to save. Have a conversation first.")
                else:
                    st.warning("No conversation to save.")
            
            if st.button("🔄 Reset Conversation"):
                st.session_state.voice_assistant.conversation_history = []
                st.success("Conversation reset.")
                st.rerun()
        
        # Text input form for typed queries
        if st.session_state.show_text_input:
            with st.form(key="text_input_form"):
                text_input = st.text_input("Type your question:", key="voice_text_input")
                submit_button = st.form_submit_button("Send")
                
                if submit_button and text_input:
                    response = st.session_state.voice_assistant.process_query(
                        text_input, 
                        context=st.session_state.analysis_results
                    )
                    st.session_state.last_response = response
                    st.session_state.last_input_method = "text"
                    st.rerun()
        
        # Display the last response (from either voice or text input)
        if "last_response" in st.session_state:
            response = st.session_state.last_response
            st.success(f"Assistant: {response['full']}")
            st.markdown("#### Voice Response:")
            st.session_state.voice_assistant.speak(response['concise'])
            st.info(f"Voice summary: {response['concise']}")
            del st.session_state.last_response

if __name__ == "__main__":
    main()
