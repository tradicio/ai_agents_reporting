import logging
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path

import yaml
from dotenv import load_dotenv
from src.pycon2026.constants import constants
from src.pycon2026.abstract.event import Event
from src.pycon2026.abstract.memory import Memory
from openai import OpenAI

logger = logging.getLogger(__name__)

load_dotenv()

_PROMPTS_PATH = Path(__file__).parent.parent / "prompts" / constants.PROMPT_FILENAME


class Agent(ABC):
    initial_state: str = "idle"
    transitions: dict[tuple[str, str], str] = {}

    def __init__(self, model: str, prompt_key: str):
        with open(_PROMPTS_PATH) as f:
            self.prompts = yaml.safe_load(f)

        self.model = model
        self.system_prompt = self.prompts[prompt_key]["system"]
        self.client = OpenAI(
            base_url=os.environ["VLLM_BASE_URL"],
            api_key="token",
        )
        self.memory = Memory()
        self._state: str = self.initial_state
        self._input_tokens: int = 0
        self._output_tokens: int = 0
        self._total_tokens: int = 0

    @property
    def state(self) -> str:
        return self._state

    def emit(self, event: Event) -> None:
        next_state = self.transitions.get((self._state, event.name))
        if next_state is not None:
            logger.info("FSM: %s -[%s]-> %s", self._state, event.name, next_state)
            self._state = next_state
        else:
            logger.warning("No FSM transition for state=%s, event=%s", self._state, event.name)

    def _reset(self) -> None:
        self._state = self.initial_state
        self.memory.clear()
        self._input_tokens = 0
        self._output_tokens = 0
        self._total_tokens = 0

    def _accumulate_tokens(self, response) -> None:
        if response.usage:
            self._input_tokens += response.usage.prompt_tokens
            self._output_tokens += response.usage.completion_tokens
            self._total_tokens += response.usage.total_tokens

    @abstractmethod
    def run(self, task: str) -> str:
        """Run the agent on a task and return the final answer."""

    def _call_llm(self, messages: list[dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": self.system_prompt}] + messages,
        )
        self._accumulate_tokens(response)
        content = response.choices[0].message.content
        logger.info("LLM response (%d chars):\n%s", len(content), content)
        return content

    def __call__(self, task: str) -> str:
        self._reset()
        start = time.monotonic()
        result = self.run(task)
        elapsed = time.monotonic() - start
        logger.info(
            "Tokens — input: %d, output: %d, total: %d | elapsed: %.2fs",
            self._input_tokens, self._output_tokens, self._total_tokens, elapsed,
        )
        return result
