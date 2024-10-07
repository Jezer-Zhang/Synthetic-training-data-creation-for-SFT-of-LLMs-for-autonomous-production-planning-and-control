from agents.agent import OperationAgent, ManagerAgent
from utilizes import load_json
import json
import pandas as pd
from datetime import datetime


# intialize agent
def instantiate_agent(agent_id, sys_prompt_path):
    if agent_id in ["Island I", "Island II", "Island III", "Robotino"]:
        return OperationAgent(agent_id, sys_prompt_path)
    elif agent_id == "Manager":
        return ManagerAgent(agent_id, sys_prompt_path)
    else:
        raise ValueError(f"Unknown agent_id: {agent_id}")


# process resposnes from llm
def preprocess_response(response: str) -> dict:
    """
    Preprocess and unite multi JSON objects in response.
    """
    if "```json" in response and "```" in response:
        response = response.replace("```json", "").replace("```", "").strip()

    lines = response.strip().split("\n")
    lines = [line for line in lines if line != "Output:"]

    commands = []
    reasons = []

    if lines[0] == "{" and lines[-1] == "}":
        response = "".join(lines)
        lines = [response]

    for line in lines:
        line = line.strip()
        if not line or line == ",":
            continue
        try:
            obj = json.loads(line)
            command = obj["command"]
            if isinstance(command, list):
                command = ", ".join(command)
            commands.append(command)
            reasons.append(obj["reason"])
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON lines: {lines}, error: {e}")
            continue

    combined_response = {"command": ", ".join(commands), "reason": "|".join(reasons)}
    combined_response["command"] = (
        combined_response["command"].replace("[", "").replace("]", "")
    )
    return combined_response


# process results and save them
def process_test_data(agent, test_points, model, operator_results, manager_results):
    for test_point in test_points:
        user_prompt = test_point["content"]
        try:
            response = agent.generate_response(user_prompt, model)

            if agent.agent_id in ["Island I", "Island II", "Island III", "Robotino"]:
                response = preprocess_response(response)
                operator_results.append(
                    {
                        "agent_id": agent.agent_id,
                        "test point number": test_point["test_point_Nr."],
                        "type": test_point["type"],
                        "content": test_point["content"],
                        "command": response.get("command", ""),
                        "reason": response.get("reason", ""),
                    }
                )
            elif agent.agent_id == "Manager":
                if "```json" in response and "```" in response:
                    response = (
                        response.replace("```json", "").replace("```", "").strip()
                    )
                manager_results.append(response)
        except Exception as e:
            print(
                f"Error processing test point {agent.agent_id}:{test_point}: {response}: {e}"
            )
            continue


# 主函数：用于加载不同的测试集并执行评估
def evaluate(experiment_type, fold_nr=None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 模型及文件配置
    if experiment_type == "part":
        model_name = "ft_gpt-3.5-turbo_part"
        model = "ft:gpt-3.5-turbo-0125:personal::9foL8qSo"
        sys_prompt_path = "prompts/systemPrompts_v2.json"
        test_data = load_json("eventLog/test_points_new.json")
        experiment_nr = "5"
    elif experiment_type == "split":
        model_name = f"ft_gpt-3.5-turbo_k_fold_{fold_nr}"
        dict_openai = {
            1: "ft:gpt-3.5-turbo-0125:personal::9fSekyex",
            2: "ft:gpt-3.5-turbo-0125:personal::9fjNbtDk",
            3: "ft:gpt-3.5-turbo-0125:personal::9fjjHNtY",
            4: "ft:gpt-3.5-turbo-0125:personal::9flkXD1i",
            5: "ft:gpt-3.5-turbo-0125:personal::9fm6cdV4",
            6: "ft:gpt-3.5-turbo-0125:personal::9fmcjyni",
        }
        model = dict_openai[fold_nr]
        sys_prompt_path = "prompts/systemPrompts_v2.json"
        testing_data = pd.read_csv(f"dataset/test_dataset_k_fold_{fold_nr}.csv")
        experiment_nr = "1"
    elif experiment_type == "whole":
        model_name = "gpt-3.5-turbo"
        model = "gpt-3.5-turbo-0125"
        sys_prompt_path = "prompts/systemPrompts_v3_format-minus.json"
        test_data = load_json("eventLog/test_points_new.json")
        experiment_nr = "format-minus-no-fine-tune"

    operator_results = []
    manager_results = []

    print(f"Start evaluating {experiment_type}...")

    # choose the respective dataset for different experiments
    if experiment_type == "part" or experiment_type == "whole":
        for agent_id, test_points in test_data.items():
            agent = instantiate_agent(agent_id, sys_prompt_path)
            process_test_data(
                agent, test_points, model, operator_results, manager_results
            )
    elif experiment_type == "split":
        for _, row in testing_data.iterrows():
            agent_id = str(row["agent_id"])
            test_point_nr = row["test_Nr"]
            user_prompt = row["user_msg"]
            agent = instantiate_agent(agent_id, sys_prompt_path)
            process_test_data(
                agent,
                [{"content": user_prompt, "test_point_Nr.": test_point_nr}],
                model,
                operator_results,
                manager_results,
            )

    # save final results
    df_operator = pd.DataFrame(operator_results)
    df_manager = pd.DataFrame(manager_results)
    df_combined = pd.concat([df_operator, df_manager], ignore_index=True)
    df_combined.to_csv(
        f"evaluation/results_{model_name}_{experiment_nr}_{timestamp}.csv", index=False
    )

    print(f"Finished evaluating {experiment_type}.")


# run different experiments
if __name__ == "__main__":
    # differetn experiment types: 'part', 'split', 'whole'
    evaluate(experiment_type="part")
    # evaluate(experiment_type="split", fold_nr=1)
    # evaluate(experiment_type="whole")
