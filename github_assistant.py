import os
import logging
import time

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("src.pycon2026").setLevel(logging.INFO)

from src.pycon2026.agents.react.github_assistant import GitHubAssistantAgent

model = os.environ.get("VLLM_MODEL")

task = "Review the open issues in the repository and help me comment on the ones I select."

print("Task: browse open GitHub issues and post comments\n")

print("Running GitHubAssistantAgent...")
start_time = time.time()
agent = GitHubAssistantAgent(model=model)
answer = agent(task)
print(f"\nGitHubAssistantAgent Answer:\n{answer}")
print(f"GitHubAssistantAgent took {time.time() - start_time:.2f} seconds\n")
