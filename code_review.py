import os
import logging
import time

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("src.pycon2026").setLevel(logging.INFO)

from src.pycon2026.agents.plain_llm import PlainLLM
from src.pycon2026.agents.reflection.reflection_agent import ReflectionAgent
from src.pycon2026.utils.logging_setup import setup_file_logging
setup_file_logging("code_review")

model = os.environ.get("VLLM_MODEL")

# ── Code to review ────────────────────────────────────────────────────────────

API_CLIENT = """\
# api_client.py
import requests

def fetch_user_data(user_id, cache={}):
    if user_id in cache:
        return cache[user_id]
    response = requests.get(f"http://api.example.com/users/{user_id}")
    data = response.json()
    cache[user_id] = data
    return data

def process_users(user_ids):
    results = []
    for id in user_ids:
        user = fetch_user_data(id)
        results.append(user['name'].upper())
    return results
"""

STATS = """\
# stats.py
def calculate_average(numbers):
    return sum(numbers) / len(numbers)

def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(len(items)):
            if items[i] == items[j]:
                duplicates.append(items[i])
    return list(set(duplicates))

def normalize(data):
    min_val = min(data)
    max_val = max(data)
    return [(x - min_val) / (max_val - min_val) for x in data]
"""

task = f"""\
Review the following two Python files. Identify every bug, code-quality issue, \
and potential improvement you can find, and explain how to fix each one.

--- File 1: api_client.py ---
{API_CLIENT}
--- File 2: stats.py ---
{STATS}\
"""

# ── Run both agents ────────────────────────────────────────────────────────────

print("Task: code review of api_client.py and stats.py\n")

print("Running PlainLLM...")
start_time = time.time()
plain_agent = PlainLLM(model=model)
plain_answer = plain_agent(task)
print(f"PlainLLM Answer:\n{plain_answer}\n")
print(f"PlainLLM took {time.time() - start_time:.2f} seconds\n")

print("-" * 80)

print("Running ReflectionAgent...")
start_time = time.time()
reflection_agent = ReflectionAgent(model=model)
reflection_answer = reflection_agent(task)
print(f"ReflectionAgent Answer:\n{reflection_answer}")
print(f"ReflectionAgent took {time.time() - start_time:.2f} seconds\n")