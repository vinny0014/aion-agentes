from loop_agent import AionLoopAgent

class AionLoopBuilder:
    def __init__(self):
        self.agent = AionLoopAgent()

    def build_and_run_task(self, task_id: int):
        return self.agent.run_loop(task_id)
