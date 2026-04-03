"""Fix for synchronous blocking and token limits in recommend.py"""
import os

filepath = os.path.join("backend", "routers", "recommend.py")
with open(filepath, "r", encoding="utf-8") as f:
    data = f.read()

# Replace InferenceClient with AsyncInferenceClient, and replace the dirty _get_hf_client
new_get_hf_client = """def _get_hf_client():
    global _hf_client
    if _hf_client is None and HF_TOKEN:
        try:
            from huggingface_hub import AsyncInferenceClient
            _hf_client = AsyncInferenceClient(
                model="Qwen/Qwen2.5-7B-Instruct",
                token=HF_TOKEN,
                timeout=60,
            )
        except Exception as e:
            print(f"[RECOMMEND] HF client init failed: {e}")
    return _hf_client"""

import re
data = re.sub(r'def _get_hf_client\(\):.*?return _hf_client', new_get_hf_client, data, flags=re.DOTALL)

# Since we duplicated some syntax earlier, remove any orphaned duplicate `def _get_hf_client` block if it exists
data = data.replace("""    if not HF_TOKEN:
        _hf_checked = True
        return None
    # Quick connectivity check (3s timeout) to avoid hanging
    import socket
    try:
        sock = socket.create_connection(("huggingface.co", 443), timeout=3)
        sock.close()
    except (socket.timeout, OSError):
        print("[RECOMMEND] Cannot reach huggingface.co — skipping HF client")
        _hf_checked = True
        return None
    try:
        from huggingface_hub import InferenceClient
        _hf_client = InferenceClient(
            model="Qwen/Qwen2.5-7B-Instruct",
            token=HF_TOKEN,
            timeout=30,
        )
        print("[RECOMMEND] HF client initialized successfully")
    except Exception as e:
        print(f"[RECOMMEND] HF client init failed: {e}")
    _hf_checked = True
    return _hf_client""", "")

# Now find client.chat_completion and replace with await client.chat_completion
data = data.replace('response = client.chat_completion(', 'response = await client.chat_completion(')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(data)
print("recommend.py restored to AsyncInferenceClient successfully.")
