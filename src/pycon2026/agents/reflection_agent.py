import json
import logging

from src.pycon2026.abstract import Agent

logger = logging.getLogger(__name__)
from src.pycon2026.constants import constants

# Events
from src.pycon2026.events.answer import AnswerEvent
from src.pycon2026.events.reflect import ReflectEvent
from src.pycon2026.events.save_memory import SaveMemoryEvent

# Tools
from src.pycon2026.tools.reflection import REFLECT_TOOL


class ReflectionAgent(Agent):
    initial_state = "idle"
    transitions = {
        ("idle", "reflect"): "thinking",
        ("thinking", "reflect"): "thinking",
        ("thinking", "save_memory"): "thinking",
        ("thinking", "answer"): "done",
    }

    def __init__(self, model: str):
        super().__init__(model, prompt_key="reflection")
        self.system_prompt = self.system_prompt.format(
            max_thinking_events=constants.MAX_THINKING_EVENTS
        )

    def run(self, task: str) -> str:
        messages = [{"role": "user", "content": task}]
        accumulated_reasoning: list[str] = []
        reflect_count = 0

        for thinking_step in range(constants.MAX_THINKING_EVENTS + 1):
            tool_choice = "auto" if thinking_step < constants.MAX_THINKING_EVENTS else "none"
            logger.info("Step %d/%d (tool_choice=%s)", thinking_step + 1, constants.MAX_THINKING_EVENTS + 1, tool_choice)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": self.system_prompt}] + messages,
                tools=[REFLECT_TOOL.model_dump()],
                tool_choice=tool_choice,
            )

            choice = response.choices[0]
            self._accumulate_tokens(response)

            if choice.finish_reason == "tool_calls":
                tool_call = choice.message.tool_calls[0]
                reasoning = json.loads(tool_call.function.arguments)["reasoning"]

                reflect_count += 1
                step_in = response.usage.prompt_tokens if response.usage else 0
                step_out = response.usage.completion_tokens if response.usage else 0
                logger.info(
                    "Reflection #%d: %s (%d chars) | step tokens: in=%d out=%d | running total: in=%d out=%d",
                    reflect_count, reasoning, len(reasoning),
                    step_in, step_out,
                    self._input_tokens, self._output_tokens,
                )

                self.emit(ReflectEvent(reasoning=reasoning, content=choice.message.content))
                self.memory.set("last_reasoning", reasoning)
                accumulated_reasoning.append(reasoning)

                messages.append(choice.message)
                tool_result = reasoning
                logger.info("Injecting reflection #%d as tool result context (%d chars)", reflect_count, len(tool_result))
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })

                if reflect_count >= constants.COMPRESS_AFTER_REFLECTIONS:
                    summary = "\n\n".join(
                        f"Step {i + 1}: {r}" for i, r in enumerate(accumulated_reasoning)
                    )
                    logger.info("Compressing %d reflection steps into memory", reflect_count)

                    self.emit(SaveMemoryEvent(summary=summary))
                    self.memory.set("accumulated_reasoning", summary)

                    messages = [
                        {"role": "user", "content": task},
                        {"role": "assistant", "content": f"My prior reasoning:\n{summary}"},
                    ]
                    accumulated_reasoning = []
                    reflect_count = 0
            else:
                content = choice.message.content
                logger.info("Answer produced (%d chars)", len(content))
                self.emit(AnswerEvent(content=content))
                self.memory.set("last_answer", content)
                return content
