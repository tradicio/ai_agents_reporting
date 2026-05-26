import logging

from src.pycon2026.abstract import Agent
from src.pycon2026.constants import constants
from src.pycon2026.events.answer import AnswerEvent
from src.pycon2026.events.critique import CritiqueEvent
from src.pycon2026.events.initial_response import InitialResponseEvent
from src.pycon2026.events.refined_response import RefinedResponseEvent

logger = logging.getLogger(__name__)




class ReflectionAgent(Agent):
    initial_state = "idle"
    transitions = {
        ("idle", "initial_response"): "evaluating",
        ("evaluating", "critique"): "refining",
        ("refining", "refined_response"): "evaluating",
        ("refining", "answer"): "done",
        ("evaluating", "answer"): "done",
    }

    def __init__(self, model: str):
        super().__init__(model, prompt_key="reflection")

    def run(self, task: str) -> str:
        generate_prompt = self.prompts["reflection"]["generate"].format(task=task)
        response = self._call_llm([{"role": "user", "content": generate_prompt}])
        logger.info("Initial response produced (%d chars)", len(response))
        self.emit(InitialResponseEvent(content=response))
        self.memory.set("last_response", response)

        for iteration in range(constants.MAX_THINKING_EVENTS):
            critique_prompt = self.prompts["reflection"]["critique"].format(
                task=task, response=response
            )
            critique = self._call_llm([{"role": "user", "content": critique_prompt}])
            logger.info(
                "Critique #%d (%d chars): %s",
                iteration + 1, len(critique), critique[:120],
            )
            self.emit(CritiqueEvent(content=critique))
            self.memory.set("last_critique", critique)

            if critique.strip().startswith(constants._NO_IMPROVEMENT_SENTINEL):
                logger.info("No improvement needed after iteration %d — returning", iteration + 1)
                self.emit(AnswerEvent(content=response))
                self.memory.set("last_answer", response)
                return response

            refine_prompt = self.prompts["reflection"]["refine"].format(
                task=task, response=response, critique=critique
            )
            response = self._call_llm([{"role": "user", "content": refine_prompt}])
            logger.info("Refined response #%d (%d chars)", iteration + 1, len(response))
            self.memory.set("last_response", response)

            is_last = iteration == constants.MAX_THINKING_EVENTS - 1
            if is_last:
                self.emit(AnswerEvent(content=response))
            else:
                self.emit(RefinedResponseEvent(content=response))

        self.memory.set("last_answer", response)
        return response
