import json
import logging
import os
import re

import requests
from dotenv import load_dotenv

from src.pycon2026.abstract import Agent
from src.pycon2026.constants import constants

# Events
from src.pycon2026.events.answer import AnswerEvent
from src.pycon2026.events.list_issues import ListIssuesEvent
from src.pycon2026.events.post_comment import PostCommentEvent
from src.pycon2026.events.reflect import ReflectEvent

# Tools
from src.pycon2026.tools.github import LIST_ISSUES_TOOL, POST_COMMENT_TOOL

load_dotenv()

logger = logging.getLogger(__name__)

class GitHubAssistantAgent(Agent):
    initial_state = "idle"
    transitions = {
        ("idle", "list_issues"): "issues_listed",
        ("issues_listed", "post_comment"): "commenting",
        ("issues_listed", "answer"): "done",
        ("commenting", "post_comment"): "commenting",
        ("commenting", "answer"): "done",
    }

    def __init__(self, model: str):
        super().__init__(model, prompt_key="github_assistant")
        self.github_token = os.environ["GITHUB_TOKEN"]
        self.repo = os.environ["GITHUB_REPO"]
        self.system_prompt = self.system_prompt.format(repo=self.repo)
        self._headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
        }

    def run(self, task: str) -> str:
        messages = [{"role": "user", "content": task}]
        tools = [LIST_ISSUES_TOOL.model_dump(), POST_COMMENT_TOOL.model_dump()]

        for iteration in range(constants.MAX_GITHUB_ASSISTANTS_ITERATIONS):
            logger.info("Iteration %d/%d", iteration + 1, constants.MAX_GITHUB_ASSISTANTS_ITERATIONS)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": self.system_prompt}] + messages,
                tools=tools,
                tool_choice="auto",
            )
            self._accumulate_tokens(response)
            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                thought = choice.message.content or ""
                if thought:
                    logger.info("Thought (%d chars): %s", len(thought), thought)
                    self.emit(ReflectEvent(reasoning=thought, content=None))
                    self.memory.set("last_reasoning", thought)

                tool_call = choice.message.tool_calls[0]
                args = json.loads(tool_call.function.arguments)
                messages.append(choice.message)
                tool_result = self._dispatch_tool(tool_call.function.name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })
            else:
                content = choice.message.content or ""
                match = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", content, re.DOTALL)
                if match:
                    tool_data = json.loads(match.group(1))
                    tool_name = tool_data.get("name")
                    logger.info("Fallback text tool call detected: %s", tool_name)
                    messages.append(choice.message)
                    tool_result = self._dispatch_tool(tool_name, tool_data.get("arguments", {}))
                    messages.append({
                        "role": "tool",
                        "tool_call_id": "fallback",
                        "content": tool_result,
                    })
                else:
                    logger.info("Answer produced (%d chars):\n%s", len(content), content)
                    self.emit(AnswerEvent(content=content))
                    self.memory.set("last_answer", content)
                    return content

        return "Maximum iterations reached without a final answer."

    def _dispatch_tool(self, tool_name: str, args: dict) -> str:
        if tool_name == "list_issues":
            return self._handle_list_issues()
        if tool_name == "post_comment":
            return self._handle_post_comment(args)
        logger.warning("Unknown tool call: %s", tool_name)
        return f"Unknown tool: {tool_name}"

    def _handle_list_issues(self) -> str:
        url = f"{constants.GITHUB_API}/repos/{self.repo}/issues"
        resp = requests.get(url, headers=self._headers, params={"state": "open", "per_page": 50})
        resp.raise_for_status()
        issues = resp.json()

        if not issues:
            logger.info("No open issues found.")
            self.emit(ListIssuesEvent(issues=[]))
            return "No open issues found."

        self.emit(ListIssuesEvent(issues=issues))
        self.memory.set("open_issues", issues)

        issue_summaries = [
            {
                "number": i["number"],
                "title": i["title"],
                "body": (i.get("body") or "")[:500],
                "labels": [label["name"] for label in i.get("labels", [])],
                "assignee": (i.get("assignee") or {}).get("login"),
            }
            for i in issues
        ]
        logger.info("Fetched %d open issues.", len(issues))
        return json.dumps({"issues": issue_summaries})

    def _handle_post_comment(self, args: dict) -> str:
        issue_number = int(args["issue_number"])
        comment_body = args["comment_body"]

        url = f"{constants.GITHUB_API}/repos/{self.repo}/issues/{issue_number}/comments"
        resp = requests.post(url, headers=self._headers, json={"body": comment_body})
        resp.raise_for_status()
        comment_url = resp.json().get("html_url", "")
        self.memory.set(f"comment_{issue_number}", comment_url)
        self.emit(PostCommentEvent(issue_number=issue_number, posted=True))
        logger.info("Comment posted on #%d: %s", issue_number, comment_url)
        return json.dumps({"status": "posted", "issue_number": issue_number, "url": comment_url})
