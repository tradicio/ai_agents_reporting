import logging

from src.pycon2026.abstract import Agent

logger = logging.getLogger(__name__)

class PlainLLM(Agent):

    def __init__(slf, model: str):
        super().__init__(model, prompt_key="plain_llm")

    def run(self, task: str) -> str:
        return self._answer(task)

    def _answer(self, task) -> str:
        prompt = self.prompts["plain_llm"]["answer"].format(task=task)
        return self._call_llm([{"role": "user", "content": prompt}])
