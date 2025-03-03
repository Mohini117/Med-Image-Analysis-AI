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

# Load environment variables
load_dotenv()

# Add custom CSS loader
def load_css():
    with open('styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


# Create directories for storing JSON files if they don't exist
def create_storage_directories():
    os.makedirs("data/prescriptions", exist_ok=True)
    os.makedirs("data/diagnostics", exist_ok=True)
    return "data/prescriptions", "data/diagnostics"

# Save JSON data to file
def save_json_data(data, directory, file_prefix):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{file_prefix}_{timestamp}.json"
    filepath = os.path.join(directory, filename)
    
    with open(filepath, 'w') as f:
        json.dump(data, indent=4, fp=f)
    
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
            "Timings": [<If `X` is 1, replace it with a morning time (e.g., 8 AM, 9 AM, etc.)>, <If `Y` is 1, replace it with an afternoon time (e.g., 1 PM, 2 PM, etc.)>, <If `Z` is 1, replace it with a night/evening time (e.g., 7 PM, 8 PM, etc.).>]  # Extract exact timings as per prescription  
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
            "Disease level":"<provide accurate level of particular disease>",
            "Confidence_Score": "<AI Confidence Level (0-100%)>",
            "Description": "<Brief explanation of the disease>",
            "Possible_Causes": ["<Cause 1>", "<Cause 2>", "<Cause 3>"],
            "Recommended_Actions": ["<Action 1>", "<Action 2>", "<Action 3>"]
        }
        Ensure the response is accurate and useful for a medical specialist also you are expert in the feild of diagnosis analysis and you can detect things which human diagnostic analyzer can not detect. If the image is unclear, specify that in the Description field."""

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
    prescriptions_dir, diagnostics_dir = create_storage_directories()
    
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
    
    page = st.sidebar.radio("", ["Prescription Analysis", "Diagnostic Image Analysis"])
    
    analyzer = ImageAnalyzer()

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

    else:  # Diagnostic Image Analysis
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

if __name__ == "__main__":
    main()