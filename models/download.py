from huggingface_hub import snapshot_download

model_path = snapshot_download("MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli", local_dir="./DeBERTa")
print("Model downloaded to:", model_path)
