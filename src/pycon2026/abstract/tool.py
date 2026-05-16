from pydantic import BaseModel


class ToolProperty(BaseModel):
    type: str
    description: str


class ToolParameters(BaseModel):
    type: str = "object"
    properties: dict[str, ToolProperty]
    required: list[str]


class ToolFunction(BaseModel):
    name: str
    description: str
    parameters: ToolParameters


class Tool(BaseModel):
    type: str = "function"
    function: ToolFunction
