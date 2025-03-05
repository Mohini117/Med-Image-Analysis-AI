# Medicine Image Analysis with Reminder System <br><br>
## Overview

The Medicine Image Analysis System is an AI-powered tool designed to analyze images of medicines, prescriptions, and diagnostic images. It accurately identifies medicines, extracts relevant medical information using OCR, and assists users through a voice-enabled assistant that processes queries and provides insights based on the extracted data which can then automatically set reminder and remind patient to take their pills suggested by doctor.<br><br>
## Features

* Medicine Identification: Recognizes medicines from images using advanced deep learning models.

* Prescription Analysis: Extracts text from prescriptions using OCR and provides relevant information.

* Diagnostic Image Analysis: Processes medical images for insights and recommendations.

* Voice Assistant: Answers user queries based on extracted data and medical databases.

* Composition Analysis: Extracts and displays the active ingredients and composition.

* Usage Information: Provides dosage, indications, and precautions.

* Side Effects & Warnings: Lists potential side effects and warnings based on medical databases.

* Multi-Language Support: Displays medicine information in multiple languages.

* Streamlit UI: Provides an interactive and user-friendly interface.

* Automatic Alerts: Utilizes JSON-formatted medicine data to automatically set alerts for users regarding medicine intake schedules and prescriptions.<br><br>
## Technology Stack

* Programming Language: Python

* User Interface: Streamlit

* Deep Learning Model: Llama Meta 3.2 Vision

* Computer Vision: OpenCV

* OCR for Text Extraction: Llama Meta 3.2 Vision (via Together API)

* Natural Language Processing: Transformers

* Voice Assistant: SpeechRecognition / Google TTS

* API: Together API for Llama 3.2 Vision and OCR

* Dataset: Custom medicine and diagnostic image dataset or pre-trained models<br><br>
***
# Installation

## Prerequisites
## Clone the Repository
```sh
$ git clone https://github.com/yourusername/medicine-image-analysis.git
  
$ cd medicine-image-analysis
```
Ensure you have Python installed (>=3.8) and required dependencies:
* Make sure you have make .env file with required api keys
* Create pyhton environment as follows:
```sh
# Create a virtual environment
python -m venv medicine-env

# Activate the virtual environment (Windows)
source medicine-env/Scripts/activate

# Activate the virtual environment (Mac/Linux)
source medicine-env/bin/activate
```
```sh
# Make sure you have requirements.txt file listed in repo.
pip install -r requirements.txt
```
```sh
# Application is ready to run now
$ streamlit run app.py
```
# Usage

* Upload an image of a medicine, prescription, or diagnostic scan.

* The system processes the image using Llama Meta 3.2 Vision and extracts relevant information.

* The voice assistant answers user queries based on extracted data.

* The identified medicine details and diagnostic insights are displayed interactively in Streamlit.

# Future Scope

* Integration with pharmacy databases for live updates.

* AI-powered chatbot for medicine and health-related queries.

* Enhanced accuracy with larger datasets and fine-tuned models.

* Augmented Reality (AR) for real-time medicine identification.

* Advanced medical diagnostic image analysis with AI-powered insights.

* Agentic AI for Automated Medicine Orders: Using AI agents, the system will automatically place medicine orders to pharmacists based on patient prescription data, ensuring seamless and timely medication procurement.

* Mobile SMS Alerts: Future development will enable the system to send automatic medicine reminders and prescription alerts via SMS, replacing the desktop interface for better accessibility and convenience.

# Contributors

Mohini D. Giri (Project Lead)<br>
Samiksha B. More (co-lead)
***
# UI OF MEDAI 
![Screenshot 2025-03-03 100809](https://github.com/user-attachments/assets/e686636f-6111-44ab-aa3f-bfe3cbbe3049)
![Screenshot 2025-03-03 100907](https://github.com/user-attachments/assets/a7fea8e9-8ed9-41f6-9155-88a117c6373c)
![Screenshot 2025-03-03 101215](https://github.com/user-attachments/assets/35ddf0bd-7fdb-40e9-90cf-acb0bde47de2)
![Screenshot 2025-03-03 101246](https://github.com/user-attachments/assets/0e941237-bd15-4c89-bceb-f5cd7887de43)
![Screenshot 2025-03-03 101329](https://github.com/user-attachments/assets/54492096-dab3-43f3-bbfc-358a22f0bf13)
![Screenshot 2025-03-03 101336](https://github.com/user-attachments/assets/62d9a702-381d-48b3-9158-f0874a6bfd56)
![Screenshot 2025-03-03 101402](https://github.com/user-attachments/assets/f50dad75-7ca9-4ec9-b75e-1c29ca9f8d27)
![Screenshot 2025-03-03 101409](https://github.com/user-attachments/assets/f765b34e-5250-430b-af54-7291818d8505)
![Screenshot 2025-03-03 101436](https://github.com/user-attachments/assets/0dc20d79-0acd-4285-b752-7ec8ed65ed8e)
![Screenshot 2025-03-03 101450](https://github.com/user-attachments/assets/c049daaf-fa38-42d1-884e-e7a7d435a148)
![Screenshot 2025-03-03 101502](https://github.com/user-attachments/assets/f56e7db4-b770-4ad3-af35-a2c6b9d935c6)
