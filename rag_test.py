import os
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# ChromaDB ক্লায়েন্ট
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Gemini Embedding Function
# api_key প্যারামিটারটি বাদ দিন, এটি নিজেই .env থেকে GEMINI_API_KEY পড়ে নেবে
gemini_ef = embedding_functions.GoogleGeminiEmbeddingFunction()

# পুরনো কালেকশন থাকলে মুছে ফেলা (fresh rebuild)
try:
    chroma_client.delete_collection(name="shop_knowledge")
    print("🗑️  Old collection deleted.")
except Exception:
    pass

collection = chroma_client.create_collection(
    name="shop_knowledge",
    embedding_function=gemini_ef
)

# knowledge/ ফোল্ডারের সব .txt ফাইল পড়া
knowledge_dir = "./knowledge"
all_chunks = []
all_ids = []
doc_id = 0

for filename in os.listdir(knowledge_dir):
    if filename.endswith(".txt"):
        filepath = os.path.join(knowledge_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # টেক্সটকে ছোট ছোট টুকরো করা
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50
        )
        chunks = splitter.split_text(content)
        
        for chunk in chunks:
            all_chunks.append(chunk)
            all_ids.append(f"{filename}_{doc_id}")
            doc_id += 1
        
        print(f"📄 {filename} → {len(chunks)} chunks")

# ChromaDB-তে যোগ করা
if all_chunks:
    collection.add(documents=all_chunks, ids=all_ids)
    print(f"\n✅ মোট {len(all_chunks)} chunks ChromaDB-তে সংরক্ষিত হয়েছে।")
else:
    print("⚠️ কোনো .txt ফাইল পাওয়া যায়নি।")