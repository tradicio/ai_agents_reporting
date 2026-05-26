from src.pycon2026.agents.multi_agent.reflective_sub_agent import ReflectiveSubAgent

class DocAgent(ReflectiveSubAgent):
    def __init__(self, model: str):
        super().__init__(model, prompt_key="doc_agent")

class TesterAgent(ReflectiveSubAgent):
    def __init__(self, model: str):
        super().__init__(model, prompt_key="tester_agent")
        
class DevAgent(ReflectiveSubAgent):
    def __init__(self, model: str):
        super().__init__(model, prompt_key="dev_agent")