PROMPT_FILENAME = "prompts.yaml"
GITHUB_API = "https://api.github.com"

MAX_THINKING_EVENTS = 5
COMPRESS_AFTER_REFLECTIONS = 3
MAX_GITHUB_ASSISTANTS_ITERATIONS = 20

MAX_ORCHESTRATOR_ITERATIONS = 20
MAX_SUBAGENT_REFLECTIONS = 5

# ProjectManager context management
MAX_TOOL_RESULT_CHARS = 400    # truncate individual tool results before they enter the PM context
MAX_TOOL_ARG_CONTEXT_CHARS = 200  # truncate 'context' field in tool-call arguments
MAX_PM_CONTEXT_MESSAGES = 6    # sliding window: keep original task + last N messages