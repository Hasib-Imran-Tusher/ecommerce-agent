import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# ================== কনফিগারেশন ==================
MAIN_MODEL = "gemini-3.5-flash-lite"
FALLBACK_MODEL = "gemini-3.5-flash"

TEST_PROMPT = "A customer says: 'I received a broken item, can I return it?' Reply as ShopEasy support agent in one short paragraph."


# ================== হেল্পার: Fallback লজিক ==================
def generate_with_fallback(prompt, main_model=MAIN_MODEL, fallback_model=FALLBACK_MODEL):
    start = time.time()
    used_model = main_model
    status = "success"
    try:
        response = client.models.generate_content(
            model=main_model,
            contents=prompt,
        )
    except Exception as e:
        print(f"⚠️ Main model ({main_model}) failed: {e}")
        print(f"🔄 Switching to fallback ({fallback_model})...")
        used_model = fallback_model
        status = "fallback"
        start = time.time()  # ফলের সময় নতুন করে গণনা
        response = client.models.generate_content(
            model=fallback_model,
            contents=prompt,
        )
    elapsed = (time.time() - start) * 1000
    return {
        "used_model": used_model,
        "status": status,
        "latency_ms": round(elapsed),
        "text": response.text,
    }


# ================== টেস্ট ১: স্বাভাবিক অবস্থায় মেইন মডেল ==================
print("=" * 60)
print("🔹 টেস্ট ১: মেইন মডেল দিয়ে সাধারণ রেসপন্স")
print("=" * 60)
result = generate_with_fallback(TEST_PROMPT)
print(f"Used model : {result['used_model']}")
print(f"Status     : {result['status']}")
print(f"Latency    : {result['latency_ms']} ms")
print(f"Reply      : {result['text']}\n")


# ================== টেস্ট ২: মেইন মডেল ভাঙা → ফলব্যাক ==================
print("=" * 60)
print("🔹 টেস্ট ২: মেইন মডেল ফেল করানো → ফলব্যাক")
print("=" * 60)
result = generate_with_fallback(
    TEST_PROMPT,
    main_model="gemini-invalid-model-xyz",  # ইচ্ছাকৃত ভুল
    fallback_model=FALLBACK_MODEL
)
print(f"Used model : {result['used_model']}")
print(f"Status     : {result['status']}")
print(f"Latency    : {result['latency_ms']} ms")
print(f"Reply      : {result['text']}\n")


# ================== টেস্ট ৩: দুই মডেলের পাশাপাশি তুলনা ==================
print("=" * 60)
print("🔹 টেস্ট ৩: MAIN বনাম FALLBACK গতি তুলনা")
print("=" * 60)
for m in [MAIN_MODEL, FALLBACK_MODEL]:
    start = time.time()
    resp = client.models.generate_content(model=m, contents=TEST_PROMPT)
    elapsed = (time.time() - start) * 1000
    print(f"{m:30s} → {elapsed:.0f} ms | {resp.text[:60]}...")

print("\n✅ সব টেস্ট সম্পন্ন।")