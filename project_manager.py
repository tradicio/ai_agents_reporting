import logging
import os
import time

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("src.pycon2026").setLevel(logging.INFO)

from src.pycon2026.agents.multi_agent.project_manager import ProjectManagerAgent

model = os.environ["VLLM_MODEL"]

task = (
    "Build a FastAPI CRUD endpoint for a 'books' resource. "
    "Each book has: id (int), title (str), author (str), year (int). "
    "Implement create, read (by id), list-all, update, and delete operations. "
    "Write full pytest tests for all endpoints using httpx AsyncClient. "
    "Write a README.md documenting the API."
)

print("=== ProjectManagerAgent demo ===")
print(f"Task: {task}\n")

start = time.time()
agent = ProjectManagerAgent(model=model)
answer = agent(task)

print(f"\n--- Final summary ---\n{answer}")
print(f"\nFiles written: {agent.memory.get('files_written', [])}")
print(f"Elapsed: {time.time() - start:.1f}s")
