import os
import time
import sqlite3
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

# Google Gemini
from google import genai


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Smart Medicine",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        font-size: 18px;
        margin-bottom: 25px;
    }

    .medicine-card {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #dddddd;
        margin-bottom: 15px;
    }

    .warning-box {
        padding: 15px;
        border-radius: 10px;
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# DATABASE
# ============================================================

DATABASE = "smart_medicine.db"


def create_database():

    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine TEXT,
            question TEXT,
            answer TEXT,
            date_time TEXT
        )
        """
    )

    connection.commit()
    connection.close()


def save_history(medicine, question, answer):

    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO history
        (medicine, question, answer, date_time)
        VALUES (?, ?, ?, ?)
        """,
        (
            medicine,
            question,
            answer,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    connection.commit()
    connection.close()


def get_history():

    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT medicine, question, answer, date_time
        FROM history
        ORDER BY id DESC
        """
    )

    records = cursor.fetchall()

    connection.close()

    return records


create_database()


# ============================================================
# MEDICINE DATABASE
# ============================================================

MEDICINES = {

    "Paracetamol": {
        "category": "Pain reliever / fever reducer",

        "uses": (
            "Generally used to reduce fever and relieve "
            "mild to moderate pain."
        ),

        "side_effects": (
            "Usually well tolerated when used appropriately. "
            "Excessive amounts can seriously damage the liver."
        ),

        "precautions": (
            "People with liver disease or those taking other "
            "medicines containing paracetamol should consult "
            "a healthcare professional."
        )
    },

    "Cetirizine": {
        "category": "Antihistamine",

        "uses": (
            "Generally used to relieve allergy symptoms such as "
            "sneezing, runny nose, itching and watery eyes."
        ),

        "side_effects": (
            "Drowsiness, tiredness, headache or dry mouth "
            "may occur in some people."
        ),

        "precautions": (
            "Be careful with activities requiring alertness if "
            "the medicine causes drowsiness."
        )
    },

    "Ibuprofen": {
        "category": "NSAID pain reliever",

        "uses": (
            "Generally used to relieve pain, inflammation "
            "and fever."
        ),

        "side_effects": (
            "May cause stomach upset, nausea or indigestion."
        ),

        "precautions": (
            "People with certain stomach, kidney, heart or "
            "blood-pressure problems should seek professional "
            "advice before using it."
        )
    },

    "Amoxicillin": {
        "category": "Antibiotic",

        "uses": (
            "Used to treat certain bacterial infections "
            "when prescribed by a healthcare professional."
        ),

        "side_effects": (
            "Possible effects include nausea, diarrhea "
            "and allergic reactions."
        ),

        "precautions": (
            "Should only be used when prescribed. Antibiotics "
            "do not treat viral infections."
        )
    },

    "Omeprazole": {
        "category": "Proton pump inhibitor",

        "uses": (
            "Generally used to reduce stomach acid and "
            "manage certain acid-related conditions."
        ),

        "side_effects": (
            "Headache, nausea, abdominal discomfort or "
            "diarrhea may occur."
        ),

        "precautions": (
            "Long-term use should be discussed with a "
            "healthcare professional."
        )
    },

    "Aspirin": {
        "category": "NSAID / antiplatelet medicine",

        "uses": (
            "May be used for pain and fever, and in specific "
            "situations may be prescribed to reduce blood clotting."
        ),

        "side_effects": (
            "Can cause stomach irritation and increase "
            "the risk of bleeding."
        ),

        "precautions": (
            "Should not be used casually for children or by "
            "people with certain bleeding or stomach conditions."
        )
    },

    "Azithromycin": {
        "category": "Macrolide antibiotic",

        "uses": (
            "Used for certain bacterial infections when "
            "prescribed by a healthcare professional."
        ),

        "side_effects": (
            "Nausea, diarrhea and abdominal discomfort "
            "can occur."
        ),

        "precautions": (
            "Use only according to professional advice. "
            "It does not treat viral infections."
        )
    }
}


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_gemini_client():

    api_key = None

    # First try Streamlit secrets
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass

    # Then try environment variable
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    try:
        return genai.Client(api_key=api_key)

    except Exception:
        return None


gemini_client = get_gemini_client()


# ============================================================
# GEMINI AI FUNCTION WITH RETRY
# ============================================================

def ask_gemini(medicine, question):

    if gemini_client is None:

        return (
            "Gemini API key is not configured.\n\n"
            "You can still use the Medicine Information section.\n\n"
            "To enable the AI Assistant, add your Gemini API key "
            "to the environment or Streamlit secrets."
        )

    # --------------------------------------------------------
    # AI PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are Smart Medicine, an educational medicine information assistant.

Medicine:
{medicine}

User question:
{question}

Give a clear and easy-to-understand educational answer.

Important safety rules:

1. Do not diagnose the user.
2. Do not prescribe medicines.
3. Do not provide personalized dosage instructions.
4. Do not tell the user to stop or start prescription medicine.
5. Explain important precautions when relevant.
6. Mention common side effects when relevant.
7. If the question describes an emergency, advise the person
   to seek immediate professional medical attention.
8. Clearly state that the information is educational and is
   not a substitute for a doctor or pharmacist.

Answer in simple language.
"""

    # --------------------------------------------------------
    # RETRY SETTINGS
    # --------------------------------------------------------

    max_retries = 4

    for attempt in range(max_retries):

        try:

            # ------------------------------------------------
            # GEMINI API REQUEST
            # ------------------------------------------------

            response = gemini_client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            # ------------------------------------------------
            # CHECK RESPONSE
            # ------------------------------------------------

            if response and response.text:

                return response.text

            return "No response was generated."

        except Exception as error:

            error_message = str(error)

            # ------------------------------------------------
            # TEMPORARY ERROR DETECTION
            # ------------------------------------------------

            temporary_error = (
                "503" in error_message
                or "UNAVAILABLE" in error_message
                or "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
                or "500" in error_message
                or "502" in error_message
                or "504" in error_message
            )

            # ------------------------------------------------
            # RETRY TEMPORARY ERRORS
            # ------------------------------------------------

            if temporary_error and attempt < max_retries - 1:

                wait_time = 2 ** attempt

                time.sleep(wait_time)

                continue

            # ------------------------------------------------
            # FINAL ERROR
            # ------------------------------------------------

            return (
                "Unable to get an AI response.\n\n"
                f"Error: {error_message}"
            )

    return (
        "Gemini is temporarily busy. "
        "Please try again in a few moments."
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">💊 Smart Medicine</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-Assisted Medicine Information System'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# DISCLAIMER
# ============================================================

st.warning(
    """
    ⚠️ **NOT MEDICAL ADVICE**

    Smart Medicine provides educational information only.
    It does not diagnose medical conditions, prescribe medicines,
    recommend personalized dosages, or replace a qualified doctor
    or pharmacist.

    For emergencies or serious symptoms, seek immediate medical
    attention.
    """
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("💊 Smart Medicine")

st.sidebar.write("Navigation")

page = st.sidebar.radio(
    "Select a page",
    [
        "🏠 Home",
        "🔎 Medicine Search",
        "🤖 AI Medicine Assistant",
        "📚 History",
        "ℹ️ About"
    ]
)


# ============================================================
# HOME PAGE
# ============================================================

if page == "🏠 Home":

    st.header("Welcome to Smart Medicine")

    st.write(
        """
        Smart Medicine is an AI-assisted application that helps
        users understand medicines through simple educational
        information.
        """
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Medicines Available",
            len(MEDICINES)
        )

    with col2:

        st.metric(
            "AI Assistant",
            "Available"
            if gemini_client
            else "API Required"
        )

    with col3:

        st.metric(
            "Database",
            "SQLite"
        )

    st.divider()

    st.subheader("✨ Features")

    st.markdown(
        """
        - 🔎 Search medicine information
        - 💊 View general medicine uses
        - ⚠️ View general precautions
        - 🤖 Ask questions using AI
        - 📚 Store previous questions
        - 🗃️ SQLite database
        - 🖥️ Simple Streamlit interface
        """
    )

    st.info(
        "Use the sidebar to explore the application."
    )


# ============================================================
# MEDICINE SEARCH
# ============================================================

elif page == "🔎 Medicine Search":

    st.header("🔎 Medicine Search")

    search = st.text_input(
        "Search for a medicine",
        placeholder="Example: Paracetamol"
    )

    if search:

        matching_medicines = [
            medicine
            for medicine in MEDICINES
            if search.lower() in medicine.lower()
        ]

        if matching_medicines:

            st.success(
                f"{len(matching_medicines)} medicine(s) found."
            )

            selected_medicine = st.selectbox(
                "Select medicine",
                matching_medicines
            )

            information = MEDICINES[selected_medicine]

            st.subheader(
                f"💊 {selected_medicine}"
            )

            st.write(
                f"**Category:** {information['category']}"
            )

            st.write(
                f"**General Uses:** {information['uses']}"
            )

            st.write(
                f"**Common Side Effects:** "
                f"{information['side_effects']}"
            )

            st.warning(
                f"**Precautions:** "
                f"{information['precautions']}"
            )

        else:

            st.error(
                "Medicine not found in the current database."
            )

            st.info(
                "Try another medicine name."
            )

    else:

        st.write(
            "Available medicines:"
        )

        for medicine in MEDICINES:

            st.write(f"💊 {medicine}")


# ============================================================
# AI MEDICINE ASSISTANT
# ============================================================

elif page == "🤖 AI Medicine Assistant":

    st.header("🤖 AI Medicine Assistant")

    st.write(
        """
        Ask a general educational question about a medicine.
        """
    )

    # --------------------------------------------------------
    # GEMINI CONNECTION STATUS
    # --------------------------------------------------------

    if gemini_client:

        st.success(
            "✅ Gemini AI is connected."
        )

    else:

        st.error(
            "❌ Gemini AI is not connected. "
            "Please configure GEMINI_API_KEY."
        )

    # --------------------------------------------------------
    # MEDICINE SELECTION
    # --------------------------------------------------------

    medicine = st.selectbox(
        "Select medicine",
        list(MEDICINES.keys())
    )

    # --------------------------------------------------------
    # QUESTION
    # --------------------------------------------------------

    question = st.text_area(
        "Enter your question",
        placeholder=(
            "Example: What are the uses of Paracetamol?"
        ),
        height=120
    )

    # --------------------------------------------------------
    # ASK AI BUTTON
    # --------------------------------------------------------

    if st.button(
        "🤖 Ask AI",
        type="primary"
    ):

        if not question.strip():

            st.error(
                "Please enter a question."
            )

        elif gemini_client is None:

            st.error(
                "Gemini API is not configured."
            )

        else:

            with st.spinner(
                "Getting information from Gemini AI..."
            ):

                answer = ask_gemini(
                    medicine,
                    question
                )

            st.subheader(
                "📖 AI Response"
            )

            st.write(answer)

            # ------------------------------------------------
            # SAVE QUESTION TO DATABASE
            # ------------------------------------------------

            save_history(
                medicine,
                question,
                answer
            )

            st.success(
                "Question saved to history."
            )


# ============================================================
# HISTORY PAGE
# ============================================================

elif page == "📚 History":

    st.header("📚 Question History")

    records = get_history()

    if not records:

        st.info(
            "No questions have been asked yet."
        )

    else:

        st.write(
            f"Total questions: {len(records)}"
        )

        for medicine, question, answer, date_time in records:

            with st.expander(
                f"💊 {medicine} | {date_time}"
            ):

                st.write(
                    f"**Question:** {question}"
                )

                st.write(
                    "**Answer:**"
                )

                st.write(answer)


# ============================================================
# ABOUT PAGE
# ============================================================

elif page == "ℹ️ About":

    st.header("ℹ️ About Smart Medicine")

    st.write(
        """
        Smart Medicine is a Python-based AI-assisted application
        designed to provide educational information about medicines.
        """
    )

    st.subheader("🎯 Project Objectives")

    st.markdown(
        """
        1. Provide basic medicine information.
        2. Help users understand common medicine uses.
        3. Display general precautions and side effects.
        4. Provide an AI-powered question-answering system.
        5. Store previous questions in a database.
        6. Provide a simple and user-friendly interface.
        """
    )

    st.subheader("🛠️ Technologies Used")

    st.markdown(
        """
        - Python 3.11
        - Streamlit
        - Google Gemini API
        - SQLite
        - SQLAlchemy
        - Pandas
        - NumPy
        - Scikit-learn
        - Requests
        - Python-dotenv
        - LangChain
        - LangChain Community
        """
    )

    st.subheader("⚠️ Medical Disclaimer")

    st.error(
        """
        This project is intended only for educational purposes.

        It is NOT a medical diagnosis system and NOT a replacement
        for professional healthcare.

        Always consult a qualified doctor or pharmacist for
        personalized medical advice.
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "💊 Smart Medicine | Educational AI Application"
)
