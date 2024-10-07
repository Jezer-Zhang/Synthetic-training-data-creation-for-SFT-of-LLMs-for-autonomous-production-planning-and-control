import json
import time
from datetime import datetime
import threading
import os
from together import Together
from openai import OpenAI
from utilizes import load_json
import re


class Simulator:
    def __init__(
        self,
        island_1,
        island_2,
        island_3,
        robotino,
        event_log,
        order_id="001",
        max_events=None,
        max_time=None,
    ):
        self.event_log = event_log
        self.island_1 = island_1
        self.island_2 = island_2
        self.island_3 = island_3
        self.robotino = robotino
        self.order_id = order_id
        self.manager_plan = "./evaluation/manager_test_results_gpt-4o_1.json"
        self.agent_seq = []

        self.max_events = max_events
        self.max_time = max_time
        self.running = True

        # Link the event log to this simulator
        self.event_log.set_simulator(self)

    def get_order_steps(self):
        orders = load_json(self.manager_plan)

        for order in orders:
            # 将字符串解析为字典
            order_dict = json.loads(order)
            # print(order_dict)
            # print(self.order_id)
            # print(order_dict["Order ID"])
            if order_dict["Order ID"] == self.order_id:
                return order_dict["Production Steps"]

    def get_agent(self, agent_name):
        if agent_name == "Island I":
            return self.island_1
        elif agent_name == "Island II":
            return self.island_2
        elif agent_name == "Island III":
            return self.island_3
        elif agent_name == "Robotino":
            return self.robotino

    def get_destination(self, agent_name):
        index = self.agent_seq.index(agent_name)
        new_index = index + 2
        return self.agent_seq[new_index]

    def process_new_event(self, agent):
        try:
            new_event = self.event_log.get_newest_event()
            if new_event:  # 最后一步返回 null， sop流程结束
                event_log = self.event_log.get_events(
                    filter_criteria=[agent.agent_name]
                )

                if event_log is not None:
                    response = agent.generate_response(event_log)
                    response = agent.preprocess_response(response)
                    command_name = response["command"]

                    if command_name:
                        self.event_log.add_event(
                            f"[{agent.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] {agent.agent_name} calls function: {command_name}",
                            agent,
                            NOTIFY=False,
                        )
                        agent.execute_command(response)

        except TypeError as e:
            print(f"Error processing event for {agent.agent_name}: {e}")
            # Log the error or handle it as needed without stopping the simulation

    def simulate_process(self):
        # start timer
        self.start_time = datetime.now()

        # agent_name = "Island I"
        # agent_name = "Robotino"
        # agent_name = "Island II"
        agent_name = "Island III"

        # initialise each agent
        if agent_name == "Island I":
            agent = self.get_agent(agent_name)
            event = f"[{agent_name}] [{datetime.now().strftime('%H:%M:%S')}] BG56 detects a workpiece at the infeed of conveyor C1."
            self.event_log.add_event(event, agent)

        elif agent_name == "Robotino":
            agent = self.get_agent(agent_name)
            event = f"[{agent_name}] [{datetime.now().strftime('%H:%M:%S')}] PG73 revieves request from Island I to transport workpieces."
            agent.ro_destination = "Island II"
            self.ro_mode = "out"
            self.event_log.add_event(event, agent)

        elif agent_name == "Island II":
            agent = self.get_agent(agent_name)
            event = f"[{agent_name}] [{datetime.now().strftime('%H:%M:%S')}] Robotino has docked with Island II."
            self.event_log.add_event(event, agent)

        # elif agent_name == "Robotino":
        #     agent = self.get_agent(agent_name)
        #     event = f"[{agent_name}] [{datetime.now().strftime('%H:%M:%S')}] PG73 revieves request from Island II to transport workpieces."
        #     agent.ro_destination = "Island III"
        #     self.ro_mode = "out"
        #     self.event_log.add_event(event, agent)

        elif agent_name == "Island III":
            agent = self.get_agent(agent_name)
            event = f"[{agent_name}] [{datetime.now().strftime('%H:%M:%S')}] Robotino has docked with Island III."
            self.event_log.add_event(event, agent)

        print(
            f"{agent_name} SOP is finished."
        )  # 最后一次call command 返回null，循环结束。

    def check_stop_conditions(self):
        if self.max_events and len(self.event_log.events) >= self.max_events:
            print("Maximum number of events reached. Stopping simulation.")
            self.running = False
        if (
            self.max_time
            and (datetime.now() - self.start_time).total_seconds() >= self.max_time
        ):
            print("Maximum simulation time reached. Stopping simulation.")
            self.running = False

    def stop(self):
        self.running = False

    def notify_new_event(self, agent):
        self.process_new_event(agent)


class EventLog:
    def __init__(self):
        self.events = []
        self.simulator = None

    def set_simulator(self, simulator):
        self.simulator = simulator

    def add_event(self, event, agent, NOTIFY=True):
        self.events.append(event)
        if NOTIFY:
            if self.simulator:
                self.simulator.notify_new_event(agent)

    def get_events(self, filter_criteria=None):
        if not filter_criteria:
            return self.events
        # print(f"Events: {self.events}")
        # print(f"Filter Criteria: {filter_criteria}")

        # Compile a regex to extract the content of the first set of square brackets
        bracket_pattern = re.compile(r"\[([^\]]+)\]")

        filtered_events = []
        for event in self.events:
            # ？？？
            if event is None:
                continue  # Skip None events
            if isinstance(event, list):
                # Flatten the list and process each string element
                for sub_event in event:
                    matches = bracket_pattern.findall(sub_event)
                    if matches and matches[0] in filter_criteria:
                        filtered_events.append(sub_event)
            else:
                # Process the event string directly
                matches = bracket_pattern.findall(event)
                if matches and matches[0] in filter_criteria:
                    filtered_events.append(event)

        # print(f"Filtered Events: {filtered_events}")

        # Ensure filtered_events is not empty before joining
        if filtered_events:
            event_str = "\n" + "\n".join(filtered_events) + "\n"
        else:
            event_str = None  # Explicitly return None if no events match the filter

        print(f"Event String: {event_str}")
        return event_str

    def get_newest_event(self):
        return self.events[-1] if self.events else None

    def store_event_log(self, file_path):
        with open(file_path, "w") as file:
            json.dump(self.events, file)


class Agent:
    def __init__(self, model, sys_prompt_path, agent_name, event_log):
        system_prompts = load_json(sys_prompt_path)
        self.agent_name = agent_name
        self.model = model
        self.openai_client = OpenAI()
        self.together_client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))
        self.system_prompt = system_prompts[agent_name]
        self.event_log = event_log

    def generate_response(self, user_prompt):
        if self.model.lower().startswith("gpt"):
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content
        else:
            response = self.together_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content

    def filter_events(self):
        filter_criteria = [self.agent_name]
        return self.event_log.get_events(filter_criteria)


class OperationAgent(Agent):
    def __init__(self, model, sys_prompt_path, agent_name, event_log):
        super().__init__(model, sys_prompt_path, agent_name, event_log)
        self.order_id = "001"
        self.manager_plan = "./evaluation/manager_test_results_gpt-4o_1.json"
        self.ro_destination = None
        self.ro_mode = None
        self.rfid_tags = {}
        self.command_sets = {
            "C1_run": self.C1_run,
            "C2_run": self.C2_run,
            "C3_run": self.C3_run,
            "C4_run": self.C4_run,
            "S1_release": self.S1_release,
            "S2_release": self.S2_release,
            "S3_release": self.S3_release,
            "branch_divert": self.branch_divert,
            "branch_straight": self.branch_straight,
            "robot_request": self.robot_request,
            "no_action": self.no_action,
            "manager_request": self.manager_request,
            "emergency_stop": self.emergency_stop,
            "alert_to_supervisor": self.alert_to_supervisor,
            "load_workpiece": self.load_workpiece,
            "choose_tool": self.choose_tool,
            "apply_coolant": self.apply_coolant,
            "start_spindle": self.start_spindle,
            "start_cutting": self.start_cutting,
            "stop_series": self.stop_series,
            "unload_workpiece": self.unload_workpiece,
            "replace_tool": self.replace_tool,
            "cooling": self.cooling,
            "lower_humidity": self.lower_humidity,
            "paint_request": self.paint_request,
            "start_painting": self.start_painting,
            "dry_workpiece": self.dry_workpiece,
            "read_info": self.read_info,
            "return_to_charge": self.return_to_charge,
            "navigate_to": self.navigate_to,
        }

    def preprocess_response(self, response: str) -> dict:
        """
        Preprocess and unite multi JSON objects in response

        Args:
        response (str): contains multi JSON objects, each object in a line or a single JSON object spread over multiple lines

        Return:
        dict: united command and reason
        """

        # Check and remove markdown format
        if "```json" in response and "```" in response:
            response = response.replace("```json", "").replace("```", "").strip()

        # print("Original response:\n", response)

        lines = response.strip().split("\n")
        lines = [line for line in lines if line != "Output:"]

        commands = []  # the elements inside expected to be all string.
        reasons = []

        # ensure the response in a parseable format
        # If the first line is '{', it's likely a single JSON object spread over multiple lines
        if lines[0] == "{" and lines[-1] == "}":
            response = "".join(lines)  # Combine lines to form a single JSON string
            # print("Combined response:\n", response)
            lines = [
                response
            ]  # Replace lines with a single-element list containing the combined response

        for line in lines:
            line = line.strip()  # Remove leading and trailing whitespace
            if not line or line == ",":
                continue  # Skip empty lines
            # buffer += line
            try:
                obj = json.loads(line)
                command = obj["command"]
                if isinstance(command, list):
                    command = ", ".join(
                        command
                    )  # Convert list to comma-separated string
                commands.append(command)
                reasons.append(obj["reason"])
                # buffer = ""  # Clear buffer after successful JSON load
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON lines: {lines}, error: {e}")
                # If JSON decoding fails, continue adding lines to buffer
                continue  # Continue to the next line until we can successfully decode

        combined_response = {
            "command": ", ".join(commands),
            "reason": "|".join(reasons),
        }

        # Remove square brackets from command
        combined_response["command"] = (
            combined_response["command"].replace("[", "").replace("]", "")
        )
        # print("Combined response:\n", combined_response)
        return combined_response

    def parse_command(self, command):
        # Extract the command part from the JSON
        command_str = command["command"]

        # Split the command string by commas to handle multiple function calls
        function_calls = re.findall(r"\w+\(.*?\)", command_str)

        command_names = []
        all_args = []

        for function_call in function_calls:
            # Use regex to extract the function name and arguments
            match = re.match(r"(\w+)\((.*)\)", function_call)
            if match:
                function_name = match.group(1)
                args_str = match.group(2)

                # Split arguments by commas, handling possible nested structures
                args = []
                nested = 0
                arg = ""
                for char in args_str:
                    if char == "," and nested == 0:
                        args.append(arg.strip())
                        arg = ""
                    else:
                        arg += char
                        if char == "(":
                            nested += 1
                        elif char == ")":
                            nested -= 1
                if arg:
                    args.append(arg.strip())

                # Convert arguments to appropriate types if possible
                converted_args = []
                for arg in args:
                    try:
                        converted_args.append(eval(arg))
                    except:
                        converted_args.append(arg.strip("'").strip('"'))

                command_names.append(function_name)
                all_args.append(converted_args)

        return command_names, all_args

    def execute_command(self, command_str):
        command_names, all_args = self.parse_command(command_str)
        all_events = []

        for command_name, args in zip(command_names, all_args):
            if command_name in self.command_sets:
                try:
                    event = self.command_sets[command_name](*args)
                    if event is not None:
                        all_events.append(event)
                except Exception as e:
                    print(f"Error executing command '{command_name}': {e}")
            else:
                print(f"Command '{command_name}' not found")

        # 最后一次call command会返回 event null， 至此循环结束。
        combined_events = self.combine_events(all_events)
        self.event_log.add_event(combined_events, self)

    def combine_events(self, events):
        # 合并多个事件，这里假设事件是列表形式
        combined = []

        for event in events:
            if event is not None:
                if isinstance(event, list):
                    combined.extend(event)
                else:
                    combined.append(event)
        return combined

    def get_order_by_id(self):
        orders = load_json(self.manager_plan)

        for order in orders:
            # 将字符串解析为字典
            order_dict = json.loads(order)
            # print(order_dict)
            # print(self.order_id)
            # print(order_dict["Order ID"])
            if order_dict["Order ID"] == self.order_id:
                return order_dict

    def read_info(self):
        order = self.get_order_by_id()
        if not order:
            return None
        for step in order["Production Steps"]:
            if step["Agent"] == self.agent_name:
                details = step["Details"]
                if self.agent_name == "Island II":
                    event_1 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] TF81 reads information from the workpiece. Information for processing is retrieved: {details}"
                    time.sleep(2)
                    event_2 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] BG51 detects a workpiece at stopper S2 on conveyor C1, indicating that the workpiece arrives at the CNC station."
                    event = f"{event_1}\n{event_2}"
                    return event

                elif self.agent_name == "Island I":
                    event = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] TF81 reads information from the workpiece. The RFID tag on the workpiece is authorized."
                    return event

                elif self.agent_name == "Island III":
                    event_1 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] TF81 reads information from the workpiece. Information for processing is retrieved: {details}"
                    time.sleep(2)
                    event_2 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] BG51 detects a workpiece at stopper S2 on conveyor C1, indicating that the workpiece arrives at the painting station."
                    event = f"{event_1}\n{event_2}"
                    return event

                elif self.agent_name == "Robotino":
                    event = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] The next destination is retrieved: {self.ro_destination}."
                    return event

    def C1_run(self, direction, duration):
        if self.agent_name == "Island I":
            if direction == "forward" and duration == 13:
                event_1 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] A workpiece passes BG56."
                time.sleep(3)
                event_2 = self.read_info()
                return f"{event_1}\n{event_2}"
            elif direction == "forward" and duration == 8:
                return f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] BG26 detects a workpiece at the infeed of the conveyor C2."

        elif self.agent_name == "Island II":
            if direction == "forward" and duration == 13:
                event_1 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] A workpiece passes BG56."
                time.sleep(3)
                event_2 = self.read_info()
                return f"{event_1}\n{event_2}"
            if direction == "forward" and duration == 8:
                time.sleep(1)
                event = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] BG26 detects a workpiece at the infeed of conveyor C2."
                return event
        elif self.agent_name == "Island III":
            if direction == "forward" and duration == 13:
                event_1 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] A workpiece passes BG56."
                time.sleep(3)
                event_2 = self.read_info()
                return f"{event_1}\n{event_2}"
            if direction == "forward" and duration == 8:
                time.sleep(1)
                event = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] BG26 detects a workpiece at the infeed of conveyor C2."
                return event

    def C2_run(self, direction, duration):
        if direction == "forward" and duration == 13:
            event_1 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] A workpiece passes BG26."
            event_2 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] BG21 detects a workpiece at stopper S1 on conveyor C2."
            return f"{event_1}\n{event_2}"

        elif direction == "forward" and duration == 8:
            return f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] BG27 detects a workpiece at the outlet of the conveyor C2."

        elif direction == "forward" and duration == 2:
            return f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] BG56 detects a workpiece at the infeed of conveyor C1."

    def C3_run(self, direction, duration):
        if direction == "forward" and duration == 8:
            time.sleep(2)
            event_1 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] Robotino unloads the workpiece."
            event_2 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] BG41 detects a workpiece at stopper S3."
            event = f"{event_1}\n{event_2}"
            return f"{event}"

    def C4_run(self, direction, duration):
        if direction == "forward" and duration == 8:
            return None

    def S1_release(self):
        event_1 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] stopper S1 is realeased."
        time.sleep(1)
        event_2 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] A workpiece passes BG21."
        time.sleep(1)
        event_3 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] stopper S1 is raised."
        time.sleep(3)
        event_4 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] BG42 detects a workpiece at the infeed of conveyor C4."
        time.sleep(2)
        event_5 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] Robotino has docked with {self.agent_name}."
        return f"{event_1}\n{event_2}\n{event_3}\n{event_4}\n{event_5}"

    def S2_release(self):
        event_1 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] stopper S2 is realeased."
        time.sleep(1)
        event_2 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] A workpiece passes BG51."
        time.sleep(1)
        event_3 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] stopper S2 is raised."
        return f"{event_1}\n{event_2}\n{event_3}"

    def S3_release(self):
        event_1 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] stopper S3 is realeased."
        time.sleep(1)
        event_2 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] A workpiece passes BG41."
        time.sleep(1)
        event_3 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] stopper S3 is raised."
        return f"{event_1}\n{event_2}\n{event_3}"

    def branch_divert(self):
        time.sleep(1)
        event_1 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] Branch is already set to divert the workpieces."
        if self.agent_name == "Island I":
            event_2 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] BG51 detects a workpiece at stopper S2 on conveyor C1."
            return f"{event_1}\n{event_2}"
        else:
            return event_1

    def branch_straight(self):
        return f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] Branch is already set to direct the workpieces straight."

    def robot_request(self, destination, mode):

        # communication between agents
        if destination == "Island I" and mode == "in":
            event = f"[[Robotino] {datetime.now().strftime('%H:%M:%S')}]Robotino recieves a command from {self.agent_name} to transport workpieces."

        elif destination == "Island II" and mode == "in":
            pass

    def no_action(self):
        return None

    def manager_request(self):
        # turn to manager agent for an update plan
        pass

    def emergency_stop(self):
        # stop simulation
        return f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] All the activities are stopped now."

    def alert_to_supervisor(self):
        # supervisor module?
        return None

    def load_workpiece(self):
        if self.agent_name == "Island II":
            time.sleep(2)
            return f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] The workpiece is loaded into CNC machine."

        elif self.agent_name == "Island III":
            time.sleep(2)
            return f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] PG60 detects a workpiece in position."

        elif self.agent_name == "Robotino":
            time.sleep(2)
            return f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] PG71 confirms the workpiece is securely loaded."

    def choose_tool(self, tool):
        time.sleep(2)
        return f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] PG51 detects the tool at initial position."

    def start_spindle(self, rpm):
        time.sleep(2)
        return f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] The spindle starts to rotate."

    def apply_coolant(self, mode):
        event_1 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] The coolant is applied."
        time.sleep(2)
        event_2 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] PG52 detects the correct placement of the workpiece."
        event = f"{event_1}\n{event_2}"
        return event

    def start_cutting(self, length, depth):
        time.sleep(10)
        return f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] CNC processing is finished."

    def stop_series(self):
        time.sleep(2)
        return f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] The machine is stopped."

    def unload_workpiece(self):
        if self.agent_name == "Island II":
            time.sleep(2)
            return f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] The workpiece is unloaded out of CNC machine."

        elif self.agent_name == "Island III":
            time.sleep(2)
            return f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] The workpiece is unloaded out of the painting station."

        elif self.agent_name == "Robotino":
            time.sleep(2)
            return f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] The workpiece is unloaded."

    def replace_tool(self):
        return None

    def cooling(self):
        return None

    def lower_humidity(self):
        return None

    def paint_request(self):
        return None

    def start_painting(self, color, mode):
        if mode == "coat":
            event_1 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] The workpiece is coated with {color} paint."
        else:
            event_1 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] The workpiece is painted with a {color} {mode}."
        time.sleep(10)
        event_2 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] The painting process is complete."
        return f"{event_1}\n{event_2}"

    def dry_workpiece(self):
        time.sleep(10)
        return f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] The drying process is complete."

    def return_to_charge(self):
        return None

    def navigate_to(self, destination, mode):
        time.sleep(4)
        return f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] Robotino has docked with {destination}."


class ManagerAgent(Agent):
    def __init__(self, model, sys_prompt_path, agent_name, event_log):
        super().__init__(model, sys_prompt_path, agent_name, event_log)

    def plan(self):
        pass

    def monitor(self):
        pass


if __name__ == "__main__":

    # Initialize event log
    event_log = EventLog()

    # Initialize agents with mock implementations
    island_1 = OperationAgent(
        model="gpt-4o",
        sys_prompt_path="./prompts/systemPrompts_v2.json",
        agent_name="Island I",
        event_log=event_log,
    )
    island_2 = OperationAgent(
        model="gpt-4o",
        sys_prompt_path="./prompts/systemPrompts_v2.json",
        agent_name="Island II",
        event_log=event_log,
    )
    island_3 = OperationAgent(
        model="gpt-4o",
        sys_prompt_path="./prompts/systemPrompts_v2.json",
        agent_name="Island III",
        event_log=event_log,
    )
    robotino = OperationAgent(
        model="gpt-4o",
        sys_prompt_path="./prompts/systemPrompts_v2.json",
        agent_name="Robotino",
        event_log=event_log,
    )

    # Initialize simulator
    simulator = Simulator(
        island_1, island_2, island_3, robotino, event_log, max_events=10, max_time=60
    )

    # Start simulation in a separate thread to simulate asynchronous behavior
    simulation_thread = threading.Thread(target=simulator.simulate_process)
    simulation_thread.start()

    # Wait for the simulation to complete
    simulation_thread.join()

    eventLog_path = "./eventLog/event_log_4.json"
    event_log.store_event_log(eventLog_path)
