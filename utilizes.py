import json
import logging


#     self.verify_provider_name()

# def verify_provider_name(self):
#     if not self.openai_client.api_key:
#         raise ValueError("OpenAI API key not set")
#     if not self.together_client.api_key:
#         raise ValueError("Together API key not set")


# load data from json file
def load_json(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error(f"The file {file_path} was not found.")
    except json.JSONDecodeError:
        logging.error(f"Error decoding the JSON from the file {file_path}.")
    return {}


# Function to find the agent by ID
def find_agent_by_id(agent_id, agent_specification):
    for agent in agent_specification["agents"]:
        if agent["id"] == agent_id:
            return agent
    return None


# generate sop for agent prompt
def generate_sop(
    agent, sensor_data, actuator_data, sensor_name, function_name, actuator
):
    sensor_true = sensor_data["sensors"][sensor_name]["plc"][actuator]["TRUE"]
    function_description = actuator_data["actuators"][actuator][function_name][
        "description"
    ]

    sop = (
        f"When {sensor_true}, {function_name} can be called to {function_description}."
    )
    return sop


if __name__ == "__main__":
    pass
