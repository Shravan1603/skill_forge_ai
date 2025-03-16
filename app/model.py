from langchain_groq import ChatGroq
# from langchain_huggingface import HuggingFacePipeline
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
                api_key=os.getenv("GROQ_API_KEY")  # Fetch API key from environment
            )
        # elif provider == "huggingface":
        #     llm = HuggingFacePipeline.from_model_id(
        #         model_id="gpt2",  # Replace with your desired Hugging Face model
        #         task="text-generation",
        #         device="cpu",  # Use "cuda" for GPU
        #         pipeline_kwargs={"max_length": 100}
        #     )
        elif provider == "openai":
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0,
                api_key=os.getenv("OPENAI_API_KEY")  # Fetch API key from environment
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
        #         google_api_key=os.getenv("GOOGLE_API_KEY")  # Fetch API key from environment
        #     )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Return the LLM and memory as a tuple
        return llm, memory
    except Exception as e:
        raise Exception(f"Failed to initialize model: {str(e)}")