import streamlit as st
from utils import write_message, logger
from chat import generate_response

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi, I'm your Chatbot! How can I help you?"},
        ]

def handle_submit(message: str):
    """
    Enhanced submit handler with error handling and user feedback.
    """
    if not message.strip():
        st.error("Please enter a message before submitting.")
        return

    try:
        with st.spinner('Thinking...'):
            response = generate_response(message)
            write_message('assistant', response)
    except Exception as e:
        st.error("Sorry, I encountered an error. Please try again.")
        logger.error(f"Error in handle_submit: {str(e)}")

def main():
    """Main function to run the chatbot application."""
    # Page Config
    st.set_page_config("ChatBot", page_icon="🤖")
    st.title("ChatBot")

    # Initialize session state
    initialize_session_state()

    # Display existing messages
    for message in st.session_state.messages:
        write_message(message['role'], message['content'], save=False)

    # Handle user input
    if question := st.chat_input("What is up?"):
        write_message('user', question)
        handle_submit(question)

if __name__ == "__main__":
    main()
