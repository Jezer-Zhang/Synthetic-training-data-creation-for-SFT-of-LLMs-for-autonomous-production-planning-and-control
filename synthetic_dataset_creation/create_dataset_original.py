import random
from utilizes import load_json
import json
import pandas as pd


# Load test data
test_data = load_json("eventLog/test_points_new.json")

# Lists to store results
operator_results = []
manager_results = []


for agent_id, test_points in test_data.items():
    for test_point in test_points:
        if agent_id in ["Island I", "Island II", "Island III", "Robotino"]:
            operator_results.append(
                {
                    "agent_id": agent_id,
                    "test point number": test_point["test_point_Nr."],
                    "type": test_point["type"],
                    "content": test_point["content"],
                    "command": test_point["command"],
                    "reason": test_point["reason"],
                }
            )
        elif agent_id == "Manager":
            manager_results.append(
                {
                    "agent_id": "Manager",
                    "test point number": test_point["test_point_Nr."],
                    "type": test_point["type"],
                    "content": test_point["content"],
                    "plan": test_point["plan"],
                }
            )

# Convert results to a DataFrame
df_operator = pd.DataFrame(operator_results)

# Save DataFrame to a CSV file
df_manager = pd.DataFrame(manager_results)

# Combine the DataFrames
df_combined = pd.concat([df_operator, df_manager], ignore_index=True)

df_combined = df_combined.sample(frac=1, random_state=42).reset_index(drop=True)

df_combined.to_csv(
    f"dataset/dataset_shuffled.csv",
    index=False,
)

print("Finished.")
