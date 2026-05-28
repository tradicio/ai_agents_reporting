import json
import logging
import re
from pathlib import Path

from src.pycon2026.abstract import Agent
from src.pycon2026.constants import constants
from src.pycon2026.events.answer import AnswerEvent
from src.pycon2026.events.orchestrator import (
    DelegateDevEvent,
    DelegateDocEvent,
    DelegateTesterEvent,
    OrchestratorDoneEvent,
    WriteFileEvent,
)
from src.pycon2026.agents.multi_agent.sub_agents import DevAgent, TesterAgent, DocAgent
from src.pycon2026.tools.orchestrator import (
    CALL_DEV_TOOL,
    CALL_DOC_TOOL,
    CALL_TESTER_TOOL,
    WRITE_FILE_TOOL,
)

logger = logging.getLogger(__name__)

_GENERATED_DIR = Path("generated")


class ProjectManagerAgent(Agent):
    initial_state = "idle"
    transitions = {
        ("idle", "delegate_dev"): "dev_running",
        ("idle", "delegate_tester"): "tester_running",
        ("dev_running", "delegate_dev"): "dev_running",
        ("dev_running", "delegate_tester"): "tester_running",
        ("dev_running", "delegate_doc"): "doc_running",
        ("dev_running", "write_file"): "dev_running",
        ("dev_running", "orchestrator_done"): "done",
        ("tester_running", "delegate_tester"): "tester_running",
        ("tester_running", "delegate_dev"): "dev_running",
        ("tester_running", "delegate_doc"): "doc_running",
        ("tester_running", "write_file"): "tester_running",
        ("tester_running", "orchestrator_done"): "done",
        ("doc_running", "delegate_doc"): "doc_running",
        ("doc_running", "delegate_dev"): "dev_running",
        ("doc_running", "delegate_tester"): "tester_running",
        ("doc_running", "write_file"): "doc_running",
        ("doc_running", "orchestrator_done"): "done",
    }

    def __init__(
        self,
        model: str,
        dev: DevAgent | None = None,
        tester: TesterAgent | None = None,
        doc: DocAgent | None = None,
        output_dir: Path = _GENERATED_DIR,
    ):
        super().__init__(model, prompt_key="project_manager")
        self._dev = dev or DevAgent(model=model)
        self._tester = tester or TesterAgent(model=model)
        self._doc = doc or DocAgent(model=model)
        self._output_dir = output_dir
        self._files_written: list[str] = []

    _TOOLS = [
        CALL_DEV_TOOL.model_dump(),
        CALL_TESTER_TOOL.model_dump(),
        CALL_DOC_TOOL.model_dump(),
        WRITE_FILE_TOOL.model_dump(),
    ]

    def run(self, task: str) -> str:
        self._files_written = []
        messages = [{"role": "user", "content": task}]

        for iteration in range(constants.MAX_ORCHESTRATOR_ITERATIONS):
            logger.info(
                "[ProjectManager] Iteration %d/%d (state=%s)",
                iteration + 1, constants.MAX_ORCHESTRATOR_ITERATIONS, self._state,
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": self.system_prompt}]
                + self._trim_messages(messages),
                tools=self._TOOLS,
                tool_choice="auto",
            )
            self._accumulate_tokens(response)
            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                tool_call = choice.message.tool_calls[0]
                args = json.loads(tool_call.function.arguments)
                messages.append(self._compact_tool_call_message(choice.message))
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": self._dispatch_tool(tool_call.function.name, args),
                })
            else:
                content = choice.message.content or ""
                text_tool = self._parse_text_tool_call(content)
                if text_tool is not None:
                    tool_name, args = text_tool
                    logger.info("[ProjectManager] Text-formatted tool call detected: %s", tool_name)
                    messages.append({"role": "assistant", "content": content[:constants.MAX_TOOL_RESULT_CHARS]})
                    messages.append({"role": "user", "content": f"Tool result for {tool_name}:\n{self._dispatch_tool(tool_name, args)}"})
                    continue
                logger.info("[ProjectManager] Final answer (%d chars):\n%s", len(content), content)
                self.emit(OrchestratorDoneEvent(files_written=self._files_written))
                self.emit(AnswerEvent(content=content))
                self.memory.set("last_answer", content)
                self.memory.set("files_written", self._files_written)
                return content

        logger.warning("[ProjectManager] Reached iteration limit without a final answer.")
        return "Maximum orchestrator iterations reached."

    def _dispatch_tool(self, tool_name: str, args: dict) -> str:
        handlers = {
            "call_dev": self._handle_call_dev,
            "call_tester": self._handle_call_tester,
            "call_doc_expert": self._handle_call_doc,
            "write_file": self._handle_write_file,
        }
        handler = handlers.get(tool_name)
        if handler is None:
            logger.warning("[ProjectManager] Unknown tool: %s", tool_name)
            return f"Unknown tool: {tool_name}"
        result = handler(args)
        limit = constants.MAX_TOOL_RESULT_CHARS
        return result if len(result) <= limit else result[:limit] + f"\n…[truncated, {len(result) - limit} chars omitted]"

    def _delegate(self, agent, event_cls, memory_key: str, args: dict) -> str:
        task = args.get("task", "")
        context = args.get("context", "")
        self.emit(event_cls(task_summary=task[:120]))
        logger.info("[ProjectManager] → %s: %s", type(agent).__name__, task[:80])
        result = agent(f"{task}\n\n--- Context ---\n{context}" if context else task)
        self.memory.set(memory_key, result)
        return result

    def _handle_call_dev(self, args: dict) -> str:
        return self._delegate(self._dev, DelegateDevEvent, "dev_output", args)

    def _handle_call_tester(self, args: dict) -> str:
        return self._delegate(self._tester, DelegateTesterEvent, "tester_output", args)

    def _handle_call_doc(self, args: dict) -> str:
        if not args.get("context"):
            args = dict(args, context="\n\n".join(filter(None, [
                self.memory.get("dev_output", ""),
                self.memory.get("tester_output", ""),
            ])))
        return self._delegate(self._doc, DelegateDocEvent, "doc_output", args)

    def _handle_write_file(self, args: dict) -> str:
        target = self._output_dir / Path(args["filename"]).name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(args["content"], encoding="utf-8")
        self.emit(WriteFileEvent(path=str(target)))
        self._files_written.append(str(target))
        logger.info("[ProjectManager] File written: %s (%d bytes)", target, len(args["content"]))
        return f"File written successfully: {target}"

    @staticmethod
    def _trim_messages(messages: list[dict]) -> list[dict]:
        """Keep first message (original task) + last N, dropping orphaned tool messages."""
        limit = constants.MAX_PM_CONTEXT_MESSAGES
        if len(messages) <= limit + 1:
            return messages
        tail = list(messages[-limit:])
        while tail:
            role = tail[0].get("role") if isinstance(tail[0], dict) else getattr(tail[0], "role", None)
            if role == "tool":
                tail.pop(0)
            else:
                break
        return [messages[0]] + tail

    @staticmethod
    def _compact_tool_call_message(msg) -> dict:
        """Serialize a tool-call message, truncating any large 'context' argument."""
        d = msg.model_dump() if hasattr(msg, "model_dump") else dict(msg)
        for tc in d.get("tool_calls") or []:
            try:
                args = json.loads(tc["function"]["arguments"])
                ctx = args.get("context", "")
                limit = constants.MAX_TOOL_ARG_CONTEXT_CHARS
                if isinstance(ctx, str) and len(ctx) > limit:
                    args["context"] = ctx[:limit] + "…"
                tc["function"]["arguments"] = json.dumps(args)
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        return d

    @staticmethod
    def _parse_text_tool_call(content: str) -> tuple[str, dict] | None:
        """Parse a tool call emitted as plain text instead of via the API mechanism."""
        match = re.search(r"<tool_call>\s*(.*?)(?:</tool_call>|$)", content, re.DOTALL)
        if not match:
            return None
        raw = match.group(1).strip()
        try:
            data = json.loads(raw)
            return data["name"], data.get("arguments", {})
        except (json.JSONDecodeError, KeyError):
            pass
        # Truncated response — recover what we can via regex.
        name_match = re.search(r'"name"\s*:\s*"([^"]+)"', raw)
        if not name_match:
            return None
        args: dict = {}
        task_match = re.search(r'"task"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
        if task_match:
            args["task"] = task_match.group(1).replace('\\"', '"').replace("\\n", "\n")
        return name_match.group(1), args
