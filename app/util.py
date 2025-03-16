import time
import streamlit as st

def success_msg( ):
    success_message = st.empty()  # Create a placeholder
    success_message.success("🎉 Changes saved successfully!")  # Show success message
    time.sleep(3)  # Wait for 5 seconds
    success_message.empty()  # Clear the message

def delete_msg(message):
    delete_message = st.empty()  # Create a placeholder
    st.success(f"🎉 Task '{message}' deleted successfully!")                    
    time.sleep(3)  # Wait for 5 seconds
    delete_message.empty()  # Clear the message
