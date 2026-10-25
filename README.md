# 🛍️ ShopEasy - AI Customer Support Agent

An intelligent, production-ready AI customer support chatbot for an e-commerce store, built with **FastAPI**, **Google Gemini AI**, and **RAG (Retrieval-Augmented Generation)**.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.143-green?logo=fastapi)
![Gemini](https://img.shields.io/badge/Gemini-3.5-orange?logo=google)

---

## 🚀 Key Features

- **🧠 AI-Powered Responses:** Uses Google's `gemini-3.5-flash-lite` for ultra-fast, intelligent replies.
- **🔄 Automatic Fallback:** If the main model fails, seamlessly switches to `gemini-3.5-flash`.
- **📚 RAG Knowledge Base:** Stores store policies, products, and FAQs in ChromaDB and retrieves relevant info for each query.
- **🛠️ Function Calling (Tool Use):** Checks live order status from a demo database.
- **💬 Chat Memory:** Remembers conversation history per user session.
- **🛡️ Guardrails:** Politely declines off-topic questions.
- **⚡ Error Handling:** Returns user-friendly 503 messages instead of crashing.
- **🎨 Modern Frontend:** Beautiful, responsive chat UI built with HTML, CSS, and JS.

---

## 🏗️ Project Architecture


User (Browser)
↓
Frontend (HTML/CSS/JS)
↓
FastAPI Backend (/chat)
↓
┌─────────────────────────┐
│ 1. RAG Search (Chroma) │ → Relevant store info
│ 2. Gemini AI (Main) │ → If fails...
│ 3. Gemini AI (Fallback)│ → Backup response
│ 4. Function Calling │ → check_order_status()
└─────────────────────────┘
↓
AI Response → User

text

---

## 📁 Project Structure


ecommerce-agent/
├── frontend/ # Chat UI
│ ├── index.html
│ ├── style.css
│ └── script.js
├── knowledge/ # RAG data source (.txt files)
│ ├── faq.txt
│ ├── products.txt
│ ├── return_policy.txt
│ └── shipping.txt
├── chroma_db/ # Vector DB (auto-generated)
├── venv/ # Virtual environment
├── .env # GEMINI_API_KEY (not in git)
├── .gitignore
├── main.py # FastAPI app
├── rag_setup.py # RAG ingestion script
├── requirements.txt
└── README.md

text

---

## ⚙️ Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/ecommerce-agent.git
cd ecommerce-agent
