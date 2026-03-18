from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv


load_dotenv()


llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash-image',api_key=os.getenv('GOOGLE_API_KEY'))

