from src.pycon2026.abstract import Tool, ToolFunction, ToolParameters, ToolProperty

LIST_ISSUES_TOOL = Tool(
    function=ToolFunction(
        name="list_issues",
        description="Fetch all open issues from the configured GitHub repository.",
        parameters=ToolParameters(
            properties={},
            required=[],
        ),
    )
)

POST_COMMENT_TOOL = Tool(
    function=ToolFunction(
        name="post_comment",
        description="Post a comment to a specific GitHub issue.",
        parameters=ToolParameters(
            properties={
                "issue_number": ToolProperty(
                    type="integer",
                    description="The issue number to comment on.",
                ),
                "comment_body": ToolProperty(
                    type="string",
                    description="The markdown body of the comment to post.",
                ),
            },
            required=["issue_number", "comment_body"],
        ),
    )
)
