import torch
import torch.nn as nn
import numpy as np
from copy import deepcopy
from dataset_interface import BaseModel

class PINNCore(nn.Module):
    def __init__(self, input_dim=4, hidden_dim=64):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, x):
        return self.mlp(x[:, -1, :]).squeeze(-1)

class PINNModel(BaseModel):
    def __init__(self, config):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.config = config
        params = config.get("model_params", {})
        self.model = PINNCore(**params).to(self.device)
        self.phys_lambda = params.get("lambda", 0.1) 

    def fit(self, train_loader, val_loader, config):
        train_params = config.get("train_params", {})
        lr = train_params.get("learning_rate", 0.001)
        max_epochs = train_params.get("max_epochs", 200)
        patience = train_params.get("patience", 20)

        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)

        best_val_mae = float('inf')
        best_weights = None
        patience_counter = 0

        for epoch in range(max_epochs):
            self.model.train()
            for batch_x, batch_y in train_loader:
                batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                optimizer.zero_grad()
                outputs = self.model(batch_x)
                
                # 基础 MSE Loss
                mse_loss = criterion(outputs, batch_y)
                
                # 物理单调性正则惩罚：如果 SOH 预测结果荒谬地超出初始值 1.0 则施加惩罚
                physics_loss = torch.mean(torch.relu(outputs - 1.0))
                
                loss = mse_loss + self.phys_lambda * physics_loss
                loss.backward()
                optimizer.step()

            self.model.eval()
            val_preds, val_targets = [], []
            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    batch_x = batch_x.to(self.device)
                    outputs = self.model(batch_x)
                    val_preds.append(outputs.cpu())
                    val_targets.append(batch_y.cpu())
            
            val_mae = torch.mean(torch.abs(torch.cat(val_preds) - torch.cat(val_targets))).item()

            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(f"Epoch {epoch+1}/{max_epochs} | Val MAE: {val_mae:.4f}")
                
            if val_mae < best_val_mae:
                best_val_mae = val_mae
                best_weights = deepcopy(self.model.state_dict())
                patience_counter = 0
            else:
                patience_counter += 1

            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch}. Best Val MAE: {best_val_mae:.4f}")
                break
                
        if best_weights is not None:
            self.model.load_state_dict(best_weights)

    def predict(self, x: np.ndarray) -> np.ndarray:
        self.model.eval()
        with torch.no_grad():
            x_tensor = torch.tensor(x, dtype=torch.float32).to(self.device)
            if x_tensor.dim() == 2:
                x_tensor = x_tensor.unsqueeze(0)
            return self.model(x_tensor).cpu().numpy()

    def save(self, path: str) -> None:
        torch.save(self.model, path)

    def load(self, path: str) -> None:
        self.model = torch.load(path, map_location=self.device)