from src.pycon2026.abstract import Tool, ToolFunction, ToolParameters, ToolProperty

CALL_DEV_TOOL = Tool(
    function=ToolFunction(
        name="call_dev",
        description=(
            "Delegate a coding task to the DevAgent. "
            "Use this to generate new API code, implement business logic, or produce any Python source file. "
            "Pass relevant prior outputs (e.g. requirements analysis) in context."
        ),
        parameters=ToolParameters(
            properties={
                "task": ToolProperty(type="string", description="Specific coding task for the developer agent."),
                "context": ToolProperty(type="string", description="Prior outputs or background context to include."),
            },
            required=["task"],
        ),
    )
)

CALL_TESTER_TOOL = Tool(
    function=ToolFunction(
        name="call_tester",
        description=(
            "Delegate a testing task to the TesterAgent. "
            "Use this to generate pytest test files for code produced by call_dev. "
            "Always pass the implementation code in context."
        ),
        parameters=ToolParameters(
            properties={
                "task": ToolProperty(type="string", description="Specific testing task for the tester agent."),
                "context": ToolProperty(type="string", description="The implementation code to write tests for."),
            },
            required=["task"],
        ),
    )
)

CALL_DOC_TOOL = Tool(
    function=ToolFunction(
        name="call_doc_expert",
        description=(
            "Delegate a documentation task to the DocAgent. "
            "Use this to generate README, docstrings, or API reference docs. "
            "Pass the implementation and tests in context."
        ),
        parameters=ToolParameters(
            properties={
                "task": ToolProperty(type="string", description="Specific documentation task for the doc agent."),
                "context": ToolProperty(type="string", description="Implementation code and tests to document."),
            },
            required=["task"],
        ),
    )
)

WRITE_FILE_TOOL = Tool(
    function=ToolFunction(
        name="write_file",
        description=(
            "Write a text artifact to disk inside the generated/ directory. "
            "Call this once per output file after the relevant agent has produced its content. "
            "filename must be a simple name like 'api.py', 'test_api.py', or 'README.md'."
        ),
        parameters=ToolParameters(
            properties={
                "filename": ToolProperty(type="string", description="Filename inside generated/ (e.g. 'api.py')."),
                "content": ToolProperty(type="string", description="Full text content to write to the file."),
            },
            required=["filename", "content"],
        ),
    )
)
