import json
import time
import tkinter as tk
from datetime import datetime
from plyer import notification
from tkinter import messagebox, ttk
import pyttsx3  # Text-to-speech library

# File paths
JSON_FILE = "prescription.json"

# Initialize text-to-speech engine
tts_engine = pyttsx3.init()

# Create GUI window
root = tk.Tk()
root.title("Medicine Reminder")
root.geometry("450x550")
root.configure(bg="#f0f8ff")

# Heading Label
heading_label = tk.Label(root, text="Medicine Reminder", font=("Arial", 16, "bold"), bg="#f0f8ff", fg="#2c3e50")
heading_label.pack(pady=10)

# Label to show patient name
patient_label = tk.Label(root, text="Patient: Loading...", font=("Arial", 14, "bold"), bg="#f0f8ff", fg="#2c3e50")
patient_label.pack(pady=5)

# Label to show the next medicine reminder
reminder_label = tk.Label(root, text="Checking schedule...", font=("Arial", 14), bg="#f0f8ff", fg="black")
reminder_label.pack(pady=10)

# Frame to contain the list
frame = tk.Frame(root, bg="#f0f8ff")
frame.pack(pady=10)

# Scrollable Listbox for medicine schedule
listbox = tk.Listbox(frame, font=("Arial", 12), width=50, height=10)
listbox.pack(side="left", padx=10)

# Add scrollbar
scrollbar = ttk.Scrollbar(frame, orient="vertical", command=listbox.yview)
scrollbar.pack(side="right", fill="y")
listbox.config(yscrollcommand=scrollbar.set)

# Variable to store patient name
patient_name = ""

# Function to load and process medicine schedule and patient information
def load_data_from_json():
    """Loads medicine schedule and patient information from JSON file."""
    try:
        with open(JSON_FILE, "r") as file:
            data = json.load(file)

        # Extract patient name
        global patient_name
        patient_name = data.get("Patient", {}).get("Name", "Unknown Patient")
        
        # Update patient label
        patient_label.config(text=f"Patient: {patient_name}")

        # Process medicine schedule
        medicine_schedule = {}

        for med in data.get("Medicines", []):
            name = med.get("Medicine", "Unknown Medicine")
            timings = [t.strip() for t in med.get("Timings", [])]

            formatted_timings = []
            for t in timings:
                if ":" not in t:
                    formatted_timings.append(f"{int(t):02d}:00")
                else:
                    formatted_timings.append(t)

            medicine_schedule[name] = {
                "dosage": med.get("Dosage", "Unknown Dosage"),
                "timings": formatted_timings
            }

        return medicine_schedule

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load JSON file: {e}")
        return {}

# Function to update UI with medicine schedule
def update_medicine_list():
    """Updates the listbox with medicines and timings."""
    listbox.delete(0, tk.END)
    schedule = load_data_from_json()
    
    for medicine, details in schedule.items():
        listbox.insert(tk.END, f"{medicine} - {details['dosage']} at {', '.join(details['timings'])}")

update_medicine_list()

# Function to speak the reminder
def speak_reminder(medicine, dosage):
    """Uses text-to-speech to remind the patient to take medicine."""
    try:
        global patient_name
        reminder_text = f"Hey {patient_name}, it's time to take your {medicine}, {dosage}"
        
        # Speak the reminder
        tts_engine.say(reminder_text)
        tts_engine.runAndWait()
        
        # Show pop-up
        root.after(100, lambda: messagebox.showinfo("Medicine Alert", f"⏰ {reminder_text} ⏰"))

    except Exception as e:
        messagebox.showerror("Error", f"Failed to speak reminder: {e}")

# Function to check for medicine reminders continuously
def check_medicine_reminders():
    """Checks if it's time for a medicine and updates UI accordingly."""
    schedule = load_data_from_json()  # This also updates the patient name
    current_time = datetime.now().strftime("%H:%M")

    for medicine, details in schedule.items():
        if current_time in details["timings"]:
            message = f"Time to take {medicine} - {details['dosage']}"
            
            # Show notification
            notification.notify(title="Medicine Reminder", message=message, timeout=10)
            
            # Update UI
            reminder_label.config(text=message, fg="red")
            
            # Speak the reminder
            speak_reminder(medicine, details["dosage"])

            break  # Avoid multiple triggers at the same time

    # Continue checking every 30 seconds
    root.after(30000, check_medicine_reminders)  

# Reload data button
def reload_data():
    """Reloads data from JSON file and updates UI."""
    update_medicine_list()
    messagebox.showinfo("Data Reloaded", "Patient and medicine data reloaded successfully.")

reload_button = tk.Button(root, text="Reload Data", command=reload_data, 
                         font=("Arial", 10), bg="#3498db", fg="white")
reload_button.pack(pady=5)

# Start checking reminders continuously
check_medicine_reminders()

# Run the GUI
root.mainloop()