from openai import OpenAI
import base64

client = OpenAI()

# dataset_path = "dataset/fine_tuning_dataset_OPENAI_shuffle_part.jsonl"

# step 1 : upload the dataset for fine tuning
# response = client.files.create(file=open(dataset_path, "rb"), purpose="fine-tune")
# print(response.id)


# response = client.files.list()
# print(response)

# # step 2 : start fine tuning
# training_file = "file-iHG7aEa6rV0RGpLAFwxqudOo"
# model = "gpt-3.5-turbo"
# response = client.fine_tuning.jobs.create(training_file=training_file, model=model)
# print(response)


# client.fine_tuning.jobs.list()


result_file = client.fine_tuning.jobs.retrieve(
    "ftjob-CGRn2Vx4MyIMSPf2xq0W1XfN"
).trained_tokens

print(result_file)

# result_file = "".join(result_file)
# training_log = client.files.content(result_file)
# training_log = training_log.read()

# # 解码 base64 响应
# decoded_bytes = base64.b64decode(training_log)

# # 将解码后的字节转换为字符串
# decoded_string = decoded_bytes.decode("utf-8")

# # 打印解码后的字符串
# print(decoded_string)
