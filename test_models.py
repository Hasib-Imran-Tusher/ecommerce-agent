import os
import time
from dotenv import load_dotenv
from google import genai

# .env থেকে API Key লোড করুন
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# পরীক্ষা করার জন্য মডেলের তালিকা (আপনি নিজে যোগ বা বিয়োগ করতে পারেন)
models_to_test = [
    "gemini-2.5-flash",       # মূল্য-কর্মক্ষমতা অনুপাতের দ্রুত মডেল
    "gemini-2.5-flash-lite",  # 2.5 সিরিজের সবচেয়ে দ্রুত এবং সস্তা মডেল
    "gemini-3.5-flash",       # নতুন প্রজন্মের দ্রুত মডেল
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite", 
     "gemini-3.1-flash", # নতুন প্রজন্মের লাইটওয়েট দ্রুত মডেল
]

# পরীক্ষার জন্য প্রম্পট (আপনার ই-কমার্স পরিস্থিতি অনুকরণ করুন)
test_prompt = "What is the return policy for a damaged item? Answer in one sentence."

print(f"🚀 মডেল প্রতিক্রিয়া সময় পরীক্ষা শুরু হচ্ছে...\nপ্রম্পট: {test_prompt}\n")
print("-" * 60)

results = []

for model_name in models_to_test:
    print(f"পরীক্ষা করা হচ্ছে: {model_name} ...", end=" ")
    try:
        start_time = time.time()
        
        # API অনুরোধ পাঠান
        response = client.models.generate_content(
            model=model_name,
            contents=test_prompt,
        )
        
        end_time = time.time()
        latency = (end_time - start_time) * 1000  # মিলিসেকেন্ডে রূপান্তর করুন
        
        # প্রতিক্রিয়া বিষয়বস্তু সংক্ষেপে দেখান
        reply_preview = response.text[:50].replace("\n", " ") + "..."
        
        results.append({
            "model": model_name,
            "latency_ms": latency,
            "reply": reply_preview
        })
        print(f"সম্পন্ন ✅ | সময় ব্যবধান: {latency:.0f} ms")
        
    except Exception as e:
        print(f"ব্যর্থ ❌ | ত্রুটি: {str(e)}")
        # যদি কোনো মডেল পরীক্ষায় ব্যর্থ হয়, তাহলে পরবর্তী মডেল পরীক্ষা চালিয়ে যান
        continue

# ফলাফল প্রদর্শন করুন
print("\n" + "=" * 60)
print("📊 পরীক্ষার ফলাফলের সারাংশ (দ্রুত থেকে ধীরে সাজানো):")
print("-" * 60)

if results:
    # সময় ব্যবধান অনুযায়ী সাজান
    sorted_results = sorted(results, key=lambda x: x["latency_ms"])
    
    for i, res in enumerate(sorted_results, 1):
        print(f"{i}. {res['model']}")
        print(f"   ⏱️  প্রতিক্রিয়া সময়: {res['latency_ms']:.0f} ms")
        print(f"   💬 প্রতিক্রিয়া সারাংশ: {res['reply']}")
        print()
    
    print(f"🏆 সবচেয়ে দ্রুত প্রতিক্রিয়া দেওয়া মডেল: {sorted_results[0]['model']}")
else:
    print("কোনো সফল পরীক্ষার ফলাফল নেই, অনুগ্রহ করে API Key বা নেটওয়ার্ক সংযোগ পরীক্ষা করুন।")