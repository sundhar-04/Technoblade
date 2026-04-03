"""Quick HF API diagnostic — tests token, connectivity, and model response."""
import os
import sys
from dotenv import load_dotenv

# Load from multiple possible locations
load_dotenv("backend/.env")
load_dotenv(".env")

token = os.getenv("HF_TOKEN")
print(f"1. HF_TOKEN loaded: {bool(token)}")
print(f"   Token value: {token[:10]}...{token[-4:]}" if token else "   Token: MISSING!")

if not token:
    print("FATAL: No HF_TOKEN found. Check .env file.")
    sys.exit(1)

print("\n2. Importing InferenceClient...")
try:
    from huggingface_hub import InferenceClient
    print("   OK — huggingface_hub imported")
except ImportError as e:
    print(f"   FAIL — {e}")
    sys.exit(1)

print("\n3. Creating client (timeout=30s)...")
try:
    client = InferenceClient(
        model="Qwen/Qwen2.5-7B-Instruct",
        token=token,
        timeout=30,
    )
    print(f"   OK — client created: {client}")
except Exception as e:
    print(f"   FAIL — {type(e).__name__}: {e}")
    sys.exit(1)

print("\n4. Sending test chat_completion (max_tokens=20)...")
try:
    response = client.chat_completion(
        messages=[{"role": "user", "content": "Say hello in exactly 3 words"}],
        max_tokens=20,
        temperature=0.5,
    )
    content = response.choices[0].message.content
    print(f"   OK — Model responded: '{content}'")
    print("\n✅ HuggingFace API is working correctly!")
except Exception as e:
    print(f"   FAIL — {type(e).__name__}: {e}")
    print("\n❌ HuggingFace API call failed. Possible causes:")
    print("   - Invalid/expired token")
    print("   - Model is overloaded or unavailable")
    print("   - Network/firewall blocking the request")
    sys.exit(1)
