import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types
import chromadb
from chromadb.utils import embedding_functions
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)
# --- RAG: ChromaDB কানেকশন ---
chroma_client = chromadb.PersistentClient(path="./chroma_db")
gemini_ef = embedding_functions.GoogleGeminiEmbeddingFunction()
rag_collection = chroma_client.get_collection(
    name="shop_knowledge",
    embedding_function=gemini_ef
)

app = FastAPI(title="ShopEasy Support Bot")
# --- Static Files (Frontend) সেটআপ ---
# 'frontend' ফোল্ডারের CSS/JS ফাইলগুলো '/static' path-এ সার্ভ হবে
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# রুট URL-এ index.html দেখাবে
@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")

# --- মডেল কনফিগারেশন ---
MAIN_MODEL = "gemini-3.5-flash-lite"      # দ্রুততম, প্রাইমারি চয়েস
FALLBACK_MODEL = "gemini-3.5-flash"       # মেইন ফেল করলে এটি ব্যবহার হবে

# --- ১. ডেমো ডেটাবেস ---
fake_order_database = {
    "12345": {"status": "Shipped", "expected_delivery": "2026-10-20", "item": "Blue T-Shirt"},
    "67890": {"status": "Processing", "expected_delivery": "2026-10-25", "item": "Running Shoes"},
    "11111": {"status": "Delivered", "expected_delivery": "2026-10-15", "item": "Wireless Mouse"},
}

# --- ২. পাইথন ফাংশন (Tool) ---
def check_order_status(order_id: str) -> str:
    """Use this function to find the current status and delivery date of a customer's order."""
    order = fake_order_database.get(order_id)
    if order:
        return f"Order {order_id} status: {order['status']}. Expected delivery: {order['expected_delivery']}. Item: {order['item']}."
    else:
        return f"Order {order_id} not found in our system."

# --- ৩. মেমোরি ও প্রম্পট ---
chat_sessions = {}

SYSTEM_PROMPT = """
You are a helpful and polite customer support agent for 'ShopEasy', an online e-commerce store.
Your job is to answer customer queries based on store policies and use the provided tools when necessary.

Store Information:
- Return Policy: Customers can return items within 7 days of delivery. Items must be unused and in original packaging. 
- Delivery Time: Standard delivery takes 3-5 business days. Express delivery takes 1-2 business days.
- Refund Policy: Refunds are processed within 5-7 business days after we receive the returned item.
- Shipping Cost: Free shipping for orders over $50. Otherwise, a flat $5 shipping fee applies.

Instructions:
1. If a customer asks about their order status, use the `check_order_status` tool with their order ID. Do NOT make up an order status.
2. If the user hasn't provided an order ID, ask for it.
3. If a user asks something not mentioned here or not related to orders, politely say you don't know and suggest contacting human support at support@shopeasy.com.
4. Keep answers short, clear, and friendly.
"""

class ChatRequest(BaseModel):
    session_id: str
    message: str

def get_relevant_context(query: str, n_results: int = 2) -> str:
    """
    ইউজারের প্রশ্নের সাথে সম্পর্কিত তথ্য ChromaDB থেকে খুঁজে বের করে।
    """
    try:
        results = rag_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        if results['documents'] and results['documents'][0]:
            # সব প্রাসঙ্গিক টুকরো একসাথে জোড়া লাগানো
            return "\n\n".join(results['documents'][0])
        return ""
    except Exception as e:
        print(f"⚠️ RAG query failed: {e}")
        return ""
    
# ============================================================
# হেল্পার ফাংশন: Main + Fallback লজিক
# ============================================================
def generate_with_fallback(contents, config):
    """
    প্রথমে MAIN_MODEL চেষ্টা করে। যদি কোনো এরর হয়, তবে FALLBACK_MODEL চেষ্টা করে।
    """
    try:
        response = client.models.generate_content(
            model=MAIN_MODEL,
            contents=contents,
            config=config
        )
        return response
    except Exception as e:
        print(f"⚠️ Main model ({MAIN_MODEL}) failed: {e}")
        print(f"🔄 Switching to fallback model ({FALLBACK_MODEL})...")
        
        response = client.models.generate_content(
            model=FALLBACK_MODEL,
            contents=contents,
            config=config
        )
        return response



@app.post("/chat")
def chat_with_bot(request: ChatRequest):
    session_id = request.session_id
    user_message = request.message
    
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    
    # 🌟 RAG: প্রাসঙ্গিক তথ্য খুঁজে বের করা
    relevant_context = get_relevant_context(user_message)
    
    # 🌟 প্রম্পটে RAG কনটেক্সট যুক্ত করা
    if relevant_context:
        augmented_message = f"""Relevant Store Information:
{relevant_context}

Customer Question: {user_message}

Answer using the above store information if relevant."""
    else:
        augmented_message = user_message
    
    # হিস্ট্রিতে অগমেন্টেড মেসেজ যোগ করা
    chat_sessions[session_id].append(
        types.Content(role="user", parts=[types.Part(text=augmented_message)])
    )
    
    try:
        response = generate_with_fallback(
            contents=chat_sessions[session_id],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
                tools=[check_order_status]
            )
        )
        
        final_response_text = response.text
        
        if not final_response_text:
            if response.function_calls:
                function_call = response.function_calls[0]
                if function_call.name == "check_order_status":
                    order_id = function_call.args.get("order_id")
                    tool_result = check_order_status(order_id)
                    
                    chat_sessions[session_id].append(
                        types.Content(role="model", parts=[types.Part(function_call=function_call)])
                    )
                    chat_sessions[session_id].append(
                        types.Content(role="user", parts=[types.Part(function_response=types.FunctionResponse(
                            name="check_order_status",
                            response={"result": tool_result}
                        ))])
                    )
                    
                    second_response = generate_with_fallback(
                        contents=chat_sessions[session_id],
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.3,
                            tools=[check_order_status]
                        )
                    )
                    final_response_text = second_response.text
                    
                    chat_sessions[session_id].append(
                        types.Content(role="model", parts=[types.Part(text=final_response_text)])
                    )
        
        return {"reply": final_response_text}
    
    except Exception as e:
        print(f"🚨 Critical Error in /chat: {str(e)}")
        if chat_sessions[session_id]:
            chat_sessions[session_id].pop()
        friendly_error = (
            "I'm sorry, but I'm having trouble connecting to my brain right now. "
            "Please try again in a few moments, or contact our human support team at support@shopeasy.com."
        )
        raise HTTPException(status_code=503, detail=friendly_error)


@app.post("/reset/{session_id}")
def reset_chat(session_id: str):
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    return {"status": "success", "message": f"Session {session_id} cleared."}