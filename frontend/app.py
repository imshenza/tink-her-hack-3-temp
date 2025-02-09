import streamlit as st
from dotenv import load_dotenv
import openai
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image

# Set the page configuration as the first command
st.set_page_config(page_title="Event Planner AI", layout="wide")

# Load environment variables
load_dotenv()

# OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = openai.Client(api_key=OPENAI_API_KEY)

# Function to generate PDF itinerary with user profile and proper text wrapping
def generate_pdf(itinerary_text, event_type, user_profile):
    pdf_filename = "itinerary.pdf"
    try:
        doc = SimpleDocTemplate(pdf_filename, pagesize=A4)
        styles = getSampleStyleSheet()
        content = []


        # Title with event name and user name in uppercase
        content.append(Paragraph(f"<b> EVENT ITINERARY</b>", styles["Title"]))
        content.append(Spacer(1, 12))

        # Add user profile details
        content.append(Paragraph(f"<b>User Profile:</b>", styles["Heading2"]))
        content.append(Spacer(1, 8))
        content.append(Paragraph(f"Name: {user_profile.get('name', 'Not provided').upper()}", styles["BodyText"]))
        content.append(Paragraph(f"Location: {user_profile.get('location', 'Not provided')}", styles["BodyText"]))
        content.append(Spacer(1, 12))

        # Add itinerary text with proper word wrapping
        for line in itinerary_text.split("\n"):
            content.append(Paragraph(line, styles["BodyText"]))
            content.append(Spacer(1, 8))  # Adds space between lines

        doc.build(content)
        return pdf_filename
    except Exception as e:
        print(f"Error while generating PDF: {e}")
        return None

# Streamlit UI Layout with logo on top-right corner
st.markdown("""
    <style>
    .logo {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 100;
    }
    </style>
 
""", unsafe_allow_html=True)

# Set up session state for chat history and user profile
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi, I am your event planning assistant. I will help you create a perfect itinerary for your event."},
        {"role": "assistant", "content": "What is the name of your event? "}
    ]
    st.session_state.details_confirmed = False
    st.session_state.event_type = ""
    st.session_state.user_profile = {}

# Custom styling for the page (Dark theme)
st.markdown(""" 
    <style>
    .stApp {
        background-color:rgb(255, 255, 255);  /* Dark background */
        color:rgb(0, 0, 0);  /* Light text */
        font-family: 'Arial', sans-serif;
    }
    .stChatMessage.user {
        background-color: #4caf50;  /* Green for user messages */
        border-radius: 15px;
        padding: 10px;
        max-width: 60%;
        margin-bottom: 10px;
        color:rgb(164, 164, 164);
    }
    .stChatMessage.assistant {
        background-color:rgb(74, 75, 83);  /* Blue for assistant messages */
        border-radius: 15px;
        padding: 10px;
        max-width: 60%;
        margin-bottom: 2px;
        color: #ffffff;
    }

    .stButton>button {
        background-color:rgb(83, 60, 87);  /* Purple for save button */
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 16px;
        border: none;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #7b1fa2;
    }
    .stTextInput input {
        border-radius: 10px;
        padding: 1px;
        border: 1px solid rgb(0, 0, 0);
        background-color:rgb(180, 176, 176);
        color:rgb(0, 0, 0);
    }
    .stTextInput label {
        color:rgb(28, 28, 28);
    }
    .stDownloadButton>button {
        background-color:rgb(87, 84, 83);  /* Orange for download button */
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 16px;
        border: none;
        transition: background-color 0.3s;
    }
    .stDownloadButton>button:hover {
        background-color: #e64a19;
    }
    .stMarkdown {
        color:rgb(31, 11, 55);
        font-weight: bold;
    }
    .stTextInput>div>div>input {
        max-width: 100% !important;
        background-color:rgb(255, 255, 255) !important;  /* Black background for input */
        color:rgb(0, 0, 0) !important;  /* White text */
    }
    .stContainer {
        background-color:rgb(255, 255, 255);
        border-radius: 12px;
        padding: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Page title and description
st.title("Happen- make it happpen!")
st.markdown("_Plan your perfect event with AI-powered suggestions!_")

# Collect user profile information with a Save button inside a box using st.expander
with st.container():
    if not st.session_state.user_profile.get('name'):
        # Add a box around the input fields using st.expander
        with st.expander("Enter your Profile Information", expanded=True):
            name = st.text_input("What is your name?")
            location = st.text_input("What is your location?")

            save_button = st.button("Save Profile")

            if save_button and name and location:
                st.session_state.user_profile['name'] = name
                st.session_state.user_profile['location'] = location
                st.success("Profile saved!")

# Chat UI
with st.container():
    for message in st.session_state.messages:
        role_class = "user" if message["role"] == "user" else "assistant"
        with st.chat_message(message["role"]):
            st.markdown(f'<div class="stChatMessage {role_class}">{message["content"]}</div>', unsafe_allow_html=True)

# User input
user_message = st.chat_input("Enter your message...")

if user_message:
    st.session_state.messages.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)
    
    if not st.session_state.event_type:
        # AI extracts event details from name
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": f"Extract all possible details from this event name: {user_message}"}]
        )
        st.session_state.event_type = user_message
    
    # AI generates itinerary after gathering details
    itinerary = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state.messages + [{"role": "system", "content": "Generate a detailed itinerary for this event."}]
    ).choices[0].message.content
    
    st.session_state.messages.append({"role": "assistant", "content": itinerary})
    with st.chat_message("assistant"):
        st.markdown(itinerary)
    
    # Generate PDF button
    itinerary_pdf = generate_pdf(itinerary, st.session_state.event_type, st.session_state.user_profile)
    if itinerary_pdf and os.path.exists(itinerary_pdf):
        with open(itinerary_pdf, "rb") as file:
            st.download_button("📥 Download Itinerary PDF", file, file_name="event_itinerary.pdf", mime="application/pdf")
    else:
        st.error("PDF generation failed. Please try again.")
