"""Script to remove socket check from recommend.py"""
import os

filepath = os.path.join("backend", "routers", "recommend.py")
data = open(filepath, "r", encoding="utf-8").read()

new_client_func = """def _get_hf_client():
    global _hf_client
    if _hf_client is None and HF_TOKEN:
        try:
            from huggingface_hub import InferenceClient
            _hf_client = InferenceClient(
                model="Qwen/Qwen2.5-7B-Instruct",
                token=HF_TOKEN,
                timeout=60,
            )
        except Exception as e:
            print(f"[RECOMMEND] HF client init failed: {e}")
    return _hf_client"""

import re
# We use regex to replace the def _get_hf_client() ... return _hf_client\n block
pattern = re.compile(r"def _get_hf_client\(\):(.*?)(?:return _hf_client\s*\n)", re.DOTALL)
new_data = pattern.sub(new_client_func + "\n", data)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_data)
print("Socket check removed.")
