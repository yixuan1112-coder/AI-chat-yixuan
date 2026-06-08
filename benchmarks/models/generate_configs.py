import os
import yaml

# 1. 确保目录存在
os.makedirs("benchmarks/configs", exist_ok=True)

models = ["mlp", "cnn", "lstm", "transformer", "pinn"]
tasks = ["soh", "rul"]

# 2. 循环生成 10 个基础配置文件
for model in models:
    for task in tasks:
        # 基础通用配置
        config = {
            "train_params": {
                "learning_rate": 0.001,
                "max_epochs": 200,
                "patience": 20,
                "batch_size": 64
            },
            "model_params": {
                "input_dim": 4,  # 电压、电流、温度、时间 4个特征
                "hidden_dim": 64
            }
        }
        
        # 针对特定模型的特有参数进行微调
        if model == "transformer":
            config["model_params"].pop("hidden_dim") # Transformer 叫 d_model
            config["model_params"]["d_model"] = 64
            config["model_params"]["nhead"] = 4
            config["model_params"]["num_layers"] = 2
        elif model == "lstm":
            config["model_params"]["num_layers"] = 1
        elif model == "pinn":
            config["model_params"]["lambda"] = 0.1
            
        # 写入文件
        file_path = f"benchmarks/configs/{model}_{task}.yaml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
print("✅ 10个基础配置文件已成功生成在 benchmarks/configs/ 目录下！")