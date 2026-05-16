from src.pycon2026.abstract import Tool, ToolFunction, ToolParameters, ToolProperty

REFLECT_TOOL = Tool(
    function=ToolFunction(
        name="reflect",
        description=(
            "Use this tool to reason step-by-step before answering. "
            "Call it when the task is complex, ambiguous, or requires careful analysis. "
            "Skip it for simple, factual questions."
        ),
        parameters=ToolParameters(
            properties={
                "reasoning": ToolProperty(
                    type="string",
                    description="Your internal step-by-step reasoning about the task.",
                )
            },
            required=["reasoning"],
        ),
    )
)