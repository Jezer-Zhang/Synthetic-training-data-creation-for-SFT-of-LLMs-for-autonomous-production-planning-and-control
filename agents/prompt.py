import json


class ControlPromptGenerator:
    def __init__(self, json_file, agent_id, event_log):
        self.json_file = json_file
        self.agent_id = agent_id
        self.agents = self.load_agents()
        self.system_prompt = self.generate_system_prompt()
        self.user_prompt = event_log

    def load_agents(self):
        with open(self.json_file, "r") as file:
            data = json.load(file)
        return data["agents"]

    def get_agent_by_id(self, agent_id):
        for agent in self.agents:
            if agent["id"] == agent_id:
                return agent
        return None

    def read_sop(self, sop_path):
        sop_path = "agentSpecifications/" + sop_path
        try:
            with open(sop_path, "r") as file:
                sop_content = file.read()
            return sop_content
        except FileNotFoundError:
            return "SOP file not found."

    def generate_system_prompt(self):
        agent = self.get_agent_by_id(self.agent_id)
        if not agent:
            return f"Agent with ID {self.agent_id} not found."

        goal_task = agent["goal & task"]
        sensors = agent["sensors"]
        sensor_context = agent["sensor_context"]
        actuators = agent["actuators"]
        additional_funcs = agent["addtional_func"]
        sop_path = agent["SOP"]

        sensor_context_lines = sensor_context.split("\\n")
        formatted_sensors = "\n".join(
            [f"{line.strip()}" for line in sensor_context_lines if line.strip()]
        )

        actuator_lines = []
        for actuator, functions in actuators.items():
            actuator_lines.append(f"### {actuator}:")
            for func, desc in functions.items():
                actuator_lines.append(f"- function {func}: {desc}")

        formatted_actuators = "\n".join(actuator_lines)

        additional_func_lines = []
        for func, desc in additional_funcs.items():
            additional_func_lines.append(f"- function {func}: {desc}")

        formatted_additional_funcs = "\n".join(additional_func_lines)

        sop_content = self.read_sop(sop_path)

        system_prompt = f"""
# Goal and task:
{goal_task}

# Context
## Sensors:
{formatted_sensors}
## Actuators and functions you can call:
{formatted_actuators}
## Additional functions you can call:
{formatted_additional_funcs}
## Error type
- Sensor Malfunctions: when sensors fail to work, it will return a failure notification.
- Actuator failure: when actuators fail to operate, it will return a failure notification.
- Inactivity timeout: no events happen for a duration, usually because of sensor or actuator failure. Call function alert_to_supervisor('timeout').
- Communication error: loses connection with other agents.
- Docking error: Robotino cannot dock with the island. Call function alert_to_supervisor('Docking error').

Under normal conditions, you follow the standard operation procedure (SOP) to plan and execute actions. If deviations are required due to specific circumstances, you have the flexibility to employ alternate functions.
## Standard operation procedure:
{sop_content}

# Notes:
1. Each change of sensor signal will be recorded in the event log.
2. Respond using the functions specified above.
3. When mutiple functions need to be called, they are enclosed in [] in SOP. Do not leave out functions.
4. Output your response in JSON format, providing a simple, short reason for your action.

# Instructions:
You will observe an event log in the input section and you shall generate your response in the output section.
You should follow the following input and output pattern to generate a response in JSON format and give the reason to your action, keep the reason simple and short.

Input:
// An event log will be given here.
Output:
{{"command":"function_()", "reason":"reason_for_action"}}
Now, you should generate a response based on the event log:
"""

        return system_prompt


class ManagerPromptGenerator:
    def __init__(self, json_file, agent_id, event_log):
        self.json_file = json_file
        self.agent_id = agent_id
        self.agents = self.load_agents()
        self.system_prompt = self.generate_system_prompt()
        self.user_prompt = event_log

    def load_agents(self):
        with open(self.json_file, "r") as file:
            data = json.load(file)
        return data["agents"]

    def get_agent_by_id(self, agent_id):
        for agent in self.agents:
            if agent["id"] == agent_id:
                return agent
        return None

    def read_file(self, file_path):
        file_path = "agentSpecifications/" + file_path
        try:
            with open(file_path, "r") as file:
                content = file.read()
            return content
        except FileNotFoundError:
            return "File not found."

    def generate_system_prompt(self):
        agent = self.get_agent_by_id(self.agent_id)
        if not agent:
            return f"Agent with ID {self.agent_id} not found."

        goal_task = agent["goal & task"]
        operate_agents = agent["operate_agents"]
        capabilities = agent["capabilities"]
        sop_path = agent["SOP"]
        output_format_path = agent["output_format"]

        operate_agents_lines = []
        for agent_name, task_desc in operate_agents.items():
            operate_agents_lines.append(f"### {agent_name}:\n{task_desc}")

        formatted_operate_agents = "\n".join(operate_agents_lines)

        capabilities_lines = []
        for capability, desc in capabilities.items():
            capabilities_lines.append(f"- {capability}: {desc}")

        formatted_capabilities = "\n".join(capabilities_lines)

        sop_content = self.read_file(sop_path)
        output_format_content = self.read_file(output_format_path)

        system_prompt = f"""
# Goal and Task:
{goal_task}

# Context
## Operational Agents:
{formatted_operate_agents}
## Capabilities:
{formatted_capabilities}
## Standard Operation Procedure:
{sop_content}

# Notes:
1. Island I is always the start agent.
2. The last step is always: Robotino transports processed workpieces from the final island to the Dispatching Zone.
3. When a workpiece is transported between islands, Robotino must be called to navigate from one island to the other.
4. Focus only on the agents that are involved in the production process based on the order.
5. Output your response in JSON format.

# Instructions:
You will observe an order in the input section and you shall generate your response in the output section.
You should follow the following input and output pattern to generate a response in JSON format and give the reason for your action, keeping the reason simple and short.

Input:
// An order will be given here.
Output Format:
{output_format_content}
Now, you should generate a response based on the order:
"""

        return system_prompt

    def get_prompt(self):
        prompt = f"{self.system_prompt}\nInput:\n{self.user_prompt}\nOutput:"
        return prompt


if __name__ == "__main__":

    # 生成各个 agent 的 prompt
    def generate_system_prompts(json_file, event_log):
        control_agents = ["Island I", "Island II", "Island III", "Robotino"]
        manager_agent = "Manager"

        # 用于存储生成的 prompts
        prompts = {}

        # 生成 Control Agents 的 prompts
        for agent_id in control_agents:
            generator = ControlPromptGenerator(json_file, agent_id, event_log)
            prompt = generator.system_prompt
            prompts[agent_id] = prompt

        # 生成 Manager Agent 的 prompt
        generator = ManagerPromptGenerator(json_file, manager_agent, event_log)
        prompt = generator.system_prompt
        prompts[manager_agent] = prompt

        return prompts

    # 示例 event_log
    event_log = ""

    # 示例 JSON 文件路径
    json_file = "agentSpecifications/agentSpecification.json"  # path to the JSON file

    # 生成 prompts
    prompts = generate_system_prompts(json_file, event_log)

    # Write the generated prompts to a JSON file
    with open("systemPrompts_v2.json", "w") as file:
        json.dump(prompts, file, indent=4)

    text = []
    # 输出生成的 prompts
    for agent_id, prompt in prompts.items():
        agent_prompt = f"Prompt for {agent_id}:\n{prompt}\n"
        text.append(agent_prompt)
        print(f"Prompt for {agent_id}:\n{prompt}\n")

    file_path = "systemPrompts_v2.txt"

    # 将文本列表写入文件
    with open(file_path, "w") as file:
        for line in text:
            file.write(line + "\n")
