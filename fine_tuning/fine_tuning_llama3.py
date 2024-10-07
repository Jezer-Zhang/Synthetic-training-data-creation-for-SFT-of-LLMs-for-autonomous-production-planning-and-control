import os
from together import Together

client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))

dataset_path = "dataset/fine_tuning_dataset_Llama3_shuffle_whole.jsonl"

# # step 1 : upload the dataset for fine tuning

# resp = client.files.upload(file=dataset_path)  # uploads a file
# print(resp)


# # step 2 : start fine tuning
# training_file = "file-7930518e-93cd-43d0-858c-2654a69141bb"
# model = "meta-llama/Meta-Llama-3-8B-Instruct"
# resp = client.fine_tuning.create(
#     training_file=training_file,
#     model=model,
#     n_epochs=3,
#     n_checkpoints=1,
#     batch_size=4,
#     learning_rate=1e-5,
# )

# print(resp)
