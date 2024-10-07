import os
from together import Together
from openai import OpenAI

from utilizes import load_json


class Agent:
    def __init__(self, id, sys_prompt_path):
        system_prompts = load_json(sys_prompt_path)
        self.id = (id,)
        self.openai_client = OpenAI()
        self.together_client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))
        self.system_prompt = system_prompts[id]

    def generate_response(self, user_prompt, model):
        if model.lower().startswith("gpt") or model.lower().startswith("ft:gpt"):
            completion = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
            )
            return completion.choices[0].message.content
        else:
            response = self.together_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
            )
            return response.choices[0].message.content


class OperationAgent(Agent):

    def call_AAS(self):
        pass


class ManagerAgent(Agent):
    def plan(self):
        pass

    def monitor(self):
        pass


if __name__ == "__main__":
    # Initialize the agent with a fixed system prompt
    sys_prompt_path = "systemPrompts.json"
    island_i = OperationAgent("Island I", sys_prompt_path)

    # Example of different user prompts
    user_prompts = [
        "input:[00:00:01] BG56 detects a workpiece at the infeed of conveyor C1.[00:00:01] Agent Island I calls the function C1_run('forward', 13).[00:00:02] BG56 detects a workpiece at the infeed of conveyor C1.[00:00:03] BG56 detects a workpiece at the infeed of conveyor C1.Output:",
        "input:[00:00:10] BG51 detects a workpiece at stopper S2 on conveyor C1.[00:00:10] BG57 detects a workpiece at the outlet of the conveyor C1.Output:",
    ]

    # Generate and print responses for different user prompts
    for user_prompt in user_prompts:
        response = island_i.generate_response(user_prompt, "gpt-3.5-turbo")
        print(f"User Prompt: {user_prompt}\nResponse: {response}\n")
