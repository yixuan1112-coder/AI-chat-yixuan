import argparse
import yaml
import torch
import random
import os
import sys

# 自动获取当前所在目录和外层目录
current_dir = os.path.dirname(os.path.abspath(__file__))  # 当前是 models 文件夹
benchmarks_dir = os.path.dirname(current_dir)             # 上一层是 benchmarks 文件夹

# 关键修复：把 benchmarks/data 目录加入系统路径，这样就能找到 dataset_interface.py 了
data_dir = os.path.join(benchmarks_dir, "data")
if data_dir not in sys.path:
    sys.path.insert(0, data_dir)

# 确保项目根目录也在路径中（可选，作为备用）
root_dir = os.path.dirname(benchmarks_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from torch.utils.data import DataLoader, Dataset, Subset
from dataset_interface import BatteryDataset

# 封装为 PyTorch 原生 Dataset 格式
class _TorchWrapper(Dataset):
    def __init__(self, battery_ds):
        self.ds = battery_ds
    def __len__(self):
        return len(self.ds)
    def __getitem__(self, idx):
        x, y, _ = self.ds[idx]
        return torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)

def set_seed(seed=42):
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_budget_dataloader(dataset_dir, split_config_path, split, task, budget, batch_size):
    ds = BatteryDataset(dataset_dir, split_config_path, split, task)
    
    if budget < 1.0 and split == "train":
        # 获取训练集中所有的唯一 cell_id
        all_cells = list(set([meta["cell_id"] for _, _, meta in ds._samples]))
        k = max(1, int(len(all_cells) * budget))
        
        # 按 cell 个体级别进行整体随机采样
        sampled_cells = set(random.sample(all_cells, k))
        
        # 过滤出只属于被采样 cell 的时间窗口数据
        valid_indices = [i for i, (_, _, meta) in enumerate(ds._samples) 
                         if meta["cell_id"] in sampled_cells]
        ds = Subset(ds, valid_indices)
        
    return DataLoader(_TorchWrapper(ds), batch_size=batch_size, shuffle=(split=="train"))

def main():
    parser = argparse.ArgumentParser(description="BatteryTwin Benchmark 模型训练")
    parser.add_argument("--model", type=str, required=True, choices=["mlp", "cnn", "lstm", "transformer", "pinn"])
    parser.add_argument("--task", type=str, required=True, choices=["soh", "rul"])
    parser.add_argument("--dataset_dir", type=str, required=True, help="数据集路径")
    parser.add_argument("--budget", type=float, default=1.0, help="使用的训练数据比例 (B实验)")
    args = parser.parse_args()

    set_seed(42)

    # 1. 动态加载对应的 yaml 配置文件 (使用绝对路径)
    config_path = os.path.join(benchmarks_dir, "configs", f"{args.model}_{args.task}.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"找不到配置文件: {config_path}，请先运行 generate_configs.py 创建它")
        
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # 2. 准备数据，加入 Budget 切分逻辑
    batch_size = config.get("train_params", {}).get("batch_size", 64)
    split_config = os.path.join(benchmarks_dir, "data", "split_config.json")
    
    train_loader = get_budget_dataloader(args.dataset_dir, split_config, "train", args.task, args.budget, batch_size)
    val_loader = get_budget_dataloader(args.dataset_dir, split_config, "val", args.task, 1.0, batch_size) 

    # 3. 动态加载我们写好的模型并实例化（平级目录直接导包）
    if args.model == "mlp":
        from mlp import MLPModel
        model = MLPModel(config)
    elif args.model == "cnn":
        from cnn import CNNModel
        model = CNNModel(config)
    elif args.model == "lstm":
        from lstm import LSTMModel
        model = LSTMModel(config)
    elif args.model == "transformer":
        from transformer import TransformerModel
        model = TransformerModel(config)
    elif args.model == "pinn":
        from pinn import PINNModel
        model = PINNModel(config)

    print(f"[{args.model.upper()}] 开始在 {args.task.upper()} 任务上训练 (Budget: {args.budget * 100}%)")
    
    # 4. 执行训练 (包括 early stopping)
    model.fit(train_loader, val_loader, config)

    # 5. 按照任务书约定的规范保存权重
    results_dir = os.path.join(benchmarks_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    save_path = os.path.join(results_dir, f"{args.model}_{args.task}_best.pt")
    model.save(save_path)
    print(f"模型已保存至: {save_path}")

if __name__ == "__main__":
    main()