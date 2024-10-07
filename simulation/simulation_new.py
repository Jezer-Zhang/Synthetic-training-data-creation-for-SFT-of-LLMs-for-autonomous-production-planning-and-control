from calendar import c
import json
import time
from datetime import datetime
import threading
import os
from together import Together
from openai import OpenAI

from utilizes import load_json


class Simulator:
    def __init__(
        self,
        island_1,
        island_2,
        island_3,
        robotino,
        event_log,
        max_events=None,
        max_time=None,
    ):
        self.event_log = event_log
        self.island_1 = island_1
        self.island_2 = island_2
        self.island_3 = island_3
        self.robotino = robotino

        self.max_events = max_events
        self.max_time = max_time
        self.running = True

    def get_agent(self, agent_name):
        if agent_name == "Island I":
            return self.island_1
        elif agent_name == "Island II":
            return self.island_2
        elif agent_name == "Island III":
            return self.island_3
        elif agent_name == "Robotino":
            return self.robotino

    def process_new_event(self):
        new_event = self.event_log.get_newest_event()

        # in case new event has mutiple lines
        events = new_event.split("\n")

        for event in events:
            if event.strip():  # not empty line
                new_event_agent = event.split()[0]
                agent = self.get_agent(new_event_agent)
                filtered_events = agent.filter_events()

                if filtered_events:
                    command = agent.generate_command(filtered_events)
                    agent.execute_command(command)

    def simulate_process(self):
        # intialize with island_1
        initial_event = "[Island I] [00:00:01] BG56 detects a workpiece at the infeed of conveyor C1."
        initial_agent = self.island_1
        # get command
        command = initial_agent.generate_response(initial_event)
        initial_agent.execute_command(command)
        # command-event loop
        while self.running:
            # check if new event occures?

            self.process_new_event()

            # check command
            if command or command != "no_action()":
                self.execute_command(command)

            self.check_stop_conditions()

    def process_new_event(self):
        if not self.running:
            return
        new_event = self.event_log.get_newest_event()
        if new_event:
            command = self.agent.generate_response()

            if command and command != "no_action()":
                self.event_log.add_event(
                    f"[{self.agent.id}] [{datetime.now().strftime('%H:%M:%S')}] Executing command: {command}"
                )
                self.execute_command(command)
            else:
                print("No command generated. Stopping simulation.")
                self.running = False

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


class EventLog:
    def __init__(self):
        self.events = []
        self.simulator = None

    def add_event(self, event):
        self.events.append(event)

    def get_events(self, filter_criteria=None):
        if not filter_criteria:
            return self.events
        return [
            event
            for event in self.events
            if any(crit in event.split()[0] for crit in filter_criteria)
        ]

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
            completion = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return completion.choices[0].message.content
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
        # if self.agent_name == "Island I" or "Island II" or "Island III":
        #     islands_responsible = ["Robotino"]
        #     filter_criteria = [self.agent_name] + islands_responsible
        # elif self.agent_name == "Robotino":
        #     islands_responsible = ["Island I", "Island II", "Island III"]
        #     filter_criteria = [self.agent_name] + islands_responsible
        # elif self.agent_name == "Manager":
        #     islands_responsible = ["Island I", "Island II", "Island III", "Robotino"]
        #     filter_criteria = islands_responsible
        filter_criteria = [self.agent_name]
        return self.event_log.get_events(filter_criteria)


class OperationAgent(Agent):
    def __init__(self):
        self.order_id = 0
        self.manager_plan = "evaluation/manager_test_results_gpt-4o_1.json"
        self.rfid_tags = {}
        self.command_sets = {
            "C1_run": self.C1_run,
            "C2_run": self.C2_run,
        }

    def parse_command(self, command_str):
        try:
            # separate function name and args
            if "(" in command_str and ")" in command_str:
                command_name, args_str = command_str.split("(", 1)
                args_str = args_str.rstrip(")")

                if args_str.strip() == "":
                    args = ()
                else:
                    args = eval(f"({args_str})")  # args string --> tuple
            else:
                command_name = command_str
                args = ()
            return command_name, args
        except Exception as e:
            print(f"Error parsing command '{command_str}': {e}")
            return None, None

    def execute_command(self, command_str):
        command_name, args = self.parse_command(command_str)
        if command_name in self.command_sets:
            try:
                self.command_sets[command_name](*args)
            except Exception as e:
                print(f"Error executing command '{command_str}': {e}")
        else:
            print(f"Command '{command_name}' not found")

    def load_order_rfid(self):
        data = load_json(self.manager_plan)
        # Assuming the JSON file contains an array of strings where each string is a JSON object
        order_plan = json.loads(data[self.order_id])
        self.rfid_tags = order_plan

    def read_tf81(self):
        # Handle TF81 specific action
        if self.agent_name in self.rfid_tags:
            rfid_info = self.rfid_tags[self.agent_name]
            details = rfid_info["Details"]
            if self.agent_name == "Island II" or "Island III":
                for detail in details:
                    event = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] TF81 reads information from the workpiece. Information for processing is retrieved: {detail}"
                    self.event_log.add_event(event)
            elif self.agent_name == "Island I":
                event = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] TF81 reads information from the workpiece. the RFID tag on the workpiece is authorized."
                self.event_log.add_event(event)
            elif self.agent_name == "Robotino":
                next_destintation = details[1]["To"]
                event = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')}] The next destination is retrieved: {next_destintation} ."
                self.event_log.add_event(event)

    # command causes the changes of sensor signals
    def C1_run(self, direction, duration):
        if direction == "forward" and duration == 13:
            event = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')} A workpiece passes BG56."
            time.sleep(3)
            event = self.handle_tf81(self)
            self.event_log.add_event(event)

    def C2_run(self, direction, duration):
        if direction == "forward" and duration == 13:
            event_1 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')} A workpiece passes BG26."
            event_2 = f"[{self.agent_name}] [{datetime.now().strftime('%H:%M:%S')} BG21 detects a workpiece at stopper S1 on conveyor C2."
            event = f"{event_1}\n{event_2}"
            self.event_log.add_event(event)


class ManagerAgent(Agent):
    def plan(self):
        pass

    def monitor(self):
        pass


if __name__ == "__main__":
    sensor_mapping = {}  # Define your sensor mapping
    event_log = EventLog()
    agent = Agent("Island I")
    simulator = Simulator(
        agent, event_log, max_events=5, max_time=60
    )  # 例如，最大事件数为10，最大时间为60秒
    event_log.set_simulator(simulator)

    simulator.simulate_process()  # 启动模拟过程
