import torch
import torch.nn as nn
import torch.nn.functional as F

# 5 predefined customer segments
CUSTOMER_SEGMENTS = [
    "Researcher", 
    "Impulse Buyer", 
    "Loyal Customer", 
    "Price-Sensitive", 
    "Window Shopper"
]

class BehaviorLSTMAttention(nn.Module):
    def __init__(self, input_dim=6, hidden_dim=64, num_layers=2, num_heads=4, num_classes=5):
        super(BehaviorLSTMAttention, self).__init__()
        # PyTorch equivalent of LSTM + Multi-Head Attention architecture
        self.lstm = nn.LSTM(input_size=input_dim, hidden_size=hidden_dim, 
                            num_layers=num_layers, batch_first=True, bidirectional=True)
        # Bidirectional LSTM means dimension gets doubled
        self.attention = nn.MultiheadAttention(embed_dim=hidden_dim*2, num_heads=num_heads, batch_first=True)
        self.fc1 = nn.Linear(hidden_dim*2, 32)
        self.fc2 = nn.Linear(32, num_classes)
        
    def forward(self, x):
        # x shape: (batch, seq_len, input_dim)
        lstm_out, _ = self.lstm(x)
        
        # Self-attention
        attn_output, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # Global average pooling over the sequence
        pooled = torch.mean(attn_output, dim=1)
        
        out = F.relu(self.fc1(pooled))
        out = self.fc2(out)
        return out

# Initialize an untrained model as a placeholder
model = BehaviorLSTMAttention()
model.eval()

def predict_persona(sequence_events):
    """
    Predicts the persona based on a sequence of events.
    sequence_events: list of dicts, e.g. 
    [{"click": 1, "view_duration": 12, "add_to_cart": 0, "search_query": 1, "purchase": 0, "scroll_depth": 50}]
    """
    if not sequence_events:
        return CUSTOMER_SEGMENTS[4] # Default fallback
        
    features = []
    for ev in sequence_events:
        row = [
            float(ev.get("click", 0)),
            float(ev.get("view_duration", 0)),
            float(ev.get("add_to_cart", 0)),
            float(ev.get("search_query", 0)),
            float(ev.get("purchase", 0)),
            float(ev.get("scroll_depth", 0))
        ]
        features.append(row)
        
    # Standardize to 3D Tensor: (batch_size=1, seq_len, input_dim)
    input_tensor = torch.tensor([features], dtype=torch.float32)
    
    with torch.no_grad():
        logits = model(input_tensor)
        probs = F.softmax(logits, dim=1)
        pred_idx = torch.argmax(probs, dim=1).item()
        
    return CUSTOMER_SEGMENTS[pred_idx]
