import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, firestore
from config import USE_LOCAL_DATA

st.set_page_config(page_title="Login", layout="centered")

st.title("🔐 Login Page")

email = st.text_input("Email")
password = st.text_input("Password", type="password")
submitted = st.button("Login")

if submitted:
    if USE_LOCAL_DATA:
        with open("tests/datasets/mock_users.json", "r") as f:
            users = json.load(f)
        user = next((u for u in users if u["first_name"].lower() in email.lower()), None)
        if user:
            st.success(f"Welcome back, {user['first_name']} ({user['tier']})")
        else:
            st.error("User not found")
    else:
        if not firebase_admin._apps:
            cred = credentials.Certificate("path/to/firebase-adminsdk.json")  # 🔁 update this path
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        docs = db.collection("users").stream()
        user = None
        for doc in docs:
            data = doc.to_dict()
            if data["first_name"].lower() in email.lower():
                user = data
                break
        if user:
            st.success(f"Welcome back, {user['first_name']} ({user['tier']})")
        else:
            st.error("User not found")
