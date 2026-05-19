import json
import logging

from src.pycon2026.abstract import Agent
from src.pycon2026.constants import constants
from src.pycon2026.events.answer import AnswerEvent
from src.pycon2026.events.reflect import ReflectEvent
from src.pycon2026.events.save_memory import SaveMemoryEvent
from src.pycon2026.tools.reflection import REFLECT_TOOL

logger = logging.getLogger(__name__)


class TesterAgent(Agent):
    initial_state = "idle"
    transitions = {
        ("idle", "reflect"): "thinking",
        ("thinking", "reflect"): "thinking",
        ("thinking", "save_memory"): "thinking",
        ("thinking", "answer"): "done",
    }

    def __init__(self, model: str):
        super().__init__(model, prompt_key="tester_agent")
        self.system_prompt = self.system_prompt.format(
            max_thinking_events=constants.MAX_SUBAGENT_REFLECTIONS
        )

    def run(self, task: str) -> str:
        messages = [{"role": "user", "content": task}]
        accumulated_reasoning: list[str] = []
        reflect_count = 0

        for step in range(constants.MAX_SUBAGENT_REFLECTIONS + 1):
            tool_choice = "auto" if step < constants.MAX_SUBAGENT_REFLECTIONS else "none"
            logger.info("[TesterAgent] Step %d/%d (tool_choice=%s)", step + 1, constants.MAX_SUBAGENT_REFLECTIONS + 1, tool_choice)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": self.system_prompt}] + messages,
                tools=[REFLECT_TOOL.model_dump()],
                tool_choice=tool_choice,
            )
            self._accumulate_tokens(response)
            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                tool_call = choice.message.tool_calls[0]
                reasoning = json.loads(tool_call.function.arguments)["reasoning"]
                reflect_count += 1
                logger.info("[TesterAgent] Reflection #%d (%d chars)", reflect_count, len(reasoning))

                self.emit(ReflectEvent(reasoning=reasoning, content=choice.message.content))
                self.memory.set("last_reasoning", reasoning)
                accumulated_reasoning.append(reasoning)

                messages.append(choice.message)
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": reasoning})

                if reflect_count >= constants.COMPRESS_AFTER_REFLECTIONS:
                    summary = "\n\n".join(f"Step {i + 1}: {r}" for i, r in enumerate(accumulated_reasoning))
                    logger.info("[TesterAgent] Compressing %d reflection steps into memory", reflect_count)
                    self.emit(SaveMemoryEvent(summary=summary))
                    self.memory.set("accumulated_reasoning", summary)
                    messages = [
                        {"role": "user", "content": task},
                        {"role": "assistant", "content": f"My prior reasoning:\n{summary}"},
                    ]
                    accumulated_reasoning = []
                    reflect_count = 0
            else:
                content = choice.message.content or ""
                logger.info("[TesterAgent] Answer produced (%d chars)", len(content))
                self.emit(AnswerEvent(content=content))
                self.memory.set("last_answer", content)
                return content

        return self.memory.get("last_answer", "")
