from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain.memory import ConversationBufferMemory
import streamlit as st

def llm_model(provider="groq"):
    """Initialize the LLM model and memory based on the specified provider."""
    try:
        # Initialize memory
        memory = ConversationBufferMemory(memory_key="chat_history")
        
        # Initialize the LLM based on the provider
        if provider == "groq":
            llm = ChatGroq(
                model="llama-3.1-8b-instant",
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                api_key=st.secrets["general"]["groq_api_key"]  # Fetch API key from Streamlit Secrets
            )
        elif provider == "openai":
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0,
                api_key=st.secrets["general"]["openai_api_key"]    # Fetch API key from Streamlit Secrets
            )
        elif provider == "ollama":
            llm = Ollama(
                model="llama2",  # Replace with your desired Ollama model
                temperature=0
            )
        # elif provider == "google-gemini":
        #     llm = ChatGoogleGenerativeAI(
        #         model="gemini-pro",
        #         temperature=0,
        #         google_api_key=st.secrets["GOOGLE_API_KEY"]  # Fetch API key from Streamlit Secrets
        #     )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Return the LLM and memory as a tuple
        return llm, memory
    except Exception as e:
        raise Exception(f"Failed to initialize model: {str(e)}")