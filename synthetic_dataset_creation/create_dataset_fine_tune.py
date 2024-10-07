import pandas as pd
import json

# Load system prompts
with open("prompts/systemPrompts_v2.json") as sys_file:
    system_prompts = json.load(sys_file)

# Load CSV file
df = pd.read_csv("dataset/dataset_shuffled.csv")


# Function to create assistant content for operator
def create_assistant_content(command, reason):
    return f'{{"command":"{command}", "reason":"{reason}"}}'


# Prepare the dataset lists
entries = []
entries_ft = []


# Process operator entries
def process_entries(islands, manager, for_openai=False):
    for _, row in df.iterrows():
        agent_id = str(row["agent_id"])
        test_Nr = row["test point number"]
        sys_prompt = system_prompts[str(row["agent_id"])]
        user_msg = row["content"]

        if agent_id in islands:
            assis_label = create_assistant_content(row["command"], row["reason"])
            entries.append(
                {
                    "agent_id": agent_id,
                    "test_Nr": test_Nr,
                    "user_msg": user_msg,
                    "command": row["command"],
                    "reason": row["reason"],
                }
            )
            if for_openai:
                entries_ft.append(
                    {
                        "messages": [
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": user_msg},
                            {"role": "assistant", "content": assis_label},
                        ]
                    }
                )
            else:
                text = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{sys_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n{user_msg}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n{assis_label}<|eot_id|>"
                entries_ft.append({"text": text})

        elif agent_id == manager:
            assis_label = row["plan"]
            entries.append(
                {
                    "agent_id": agent_id,
                    "test_Nr": test_Nr,
                    "user_msg": user_msg,
                    "plan": row["plan"],
                }
            )
            if for_openai:
                entries_ft.append(
                    {
                        "messages": [
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": user_msg},
                            {"role": "assistant", "content": assis_label},
                        ]
                    }
                )
            else:
                text = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{sys_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n{user_msg}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n{assis_label}<|eot_id|>"
                entries_ft.append({"text": text})


# Save dataset to JSONL file
def save_jsonl(filename):
    with open(filename, "w") as outfile:
        for data in entries_ft:
            json.dump(data, outfile)
            outfile.write("\n")
    print(f"Dataset preparation complete. Saved to {filename}")


# K-fold split and save
def k_fold_split_and_save(k, for_openai=False):
    df_folds = [[] for _ in range(k)]
    df_ft_folds = [[] for _ in range(k)]

    for idx, entry in enumerate(entries):
        df_folds[idx % k].append(entry)

    for idx, entry in enumerate(entries_ft):
        df_ft_folds[idx % k].append(entry)

    def save_fold_datasets(fold_idx):
        # Save fine-tuning data
        fine_tune_data_ft = [
            entry for i in range(k) if i != fold_idx for entry in df_ft_folds[i]
        ]
        with open(
            f"dataset/fine_tuning_dataset_k_fold_{fold_idx + 1}.jsonl", "w"
        ) as fine_tune_file:
            for data in fine_tune_data_ft:
                json.dump(data, fine_tune_file)
                fine_tune_file.write("\n")
        print(f"Fold {fold_idx + 1} datasets saved.")

    for i in range(k):
        save_fold_datasets(i)


# Run based on mode
def run_mode(mode, k=6):
    if mode == "Llama3_part":
        process_entries(islands=["Island I", "Island II"], manager=None)
        save_jsonl("dataset/fine_tuning_dataset_llama3_shuffle_part.jsonl")

    elif mode == "Llama3_whole":
        process_entries(
            islands=["Island I", "Island II", "Island III", "Robotino"],
            manager="Manager",
        )
        save_jsonl("dataset/fine_tuning_dataset_Llama3_shuffle_whole.jsonl")

    elif mode == "Llama3_k_fold":
        process_entries(
            islands=["Island I", "Island II", "Island III", "Robotino"],
            manager="Manager",
        )
        k_fold_split_and_save(k)

    elif mode == "OpenAI_part":
        process_entries(
            islands=["Island I", "Island II"], manager=None, for_openai=True
        )
        save_jsonl("dataset/fine_tuning_dataset_OPENAI_shuffle_part.jsonl")

    elif mode == "OpenAI_whole":
        process_entries(
            islands=["Island I", "Island II", "Island III", "Robotino"],
            manager="Manager",
            for_openai=True,
        )
        save_jsonl("dataset/fine_tuning_dataset_OPENAI_shuffle_whole.jsonl")

    elif mode == "OpenAI_k_fold":
        process_entries(
            islands=["Island I", "Island II", "Island III", "Robotino"],
            manager="Manager",
            for_openai=True,
        )
        k_fold_split_and_save(k, for_openai=True)


# Example of running different modes
if __name__ == "__main__":
    run_mode("Llama3_k_fold")  # You can change the mode and k as needed
