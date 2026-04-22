import torch
import torch.nn as nn

class BehaviorRNN(nn.Module):
    def __init__(self, num_actions, embedding_dim=32, hidden_dim=64, num_layers=1):
        super(BehaviorRNN, self).__init__()
        self.action_embedding = nn.Embedding(num_actions, embedding_dim)
        self.rnn = nn.RNN(embedding_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, num_actions)
        
    def forward(self, x):
        # x shape: (batch_size, sequence_length)
        embedded = self.action_embedding(x)
        # embedded shape: (batch_size, sequence_length, embedding_dim)
        out, hidden = self.rnn(embedded)
        # We only care about the output from the last time step
        last_out = out[:, -1, :]
        return self.fc(last_out)

class BehaviorLSTM(nn.Module):
    def __init__(self, num_actions, embedding_dim=32, hidden_dim=64, num_layers=1):
        super(BehaviorLSTM, self).__init__()
        self.action_embedding = nn.Embedding(num_actions, embedding_dim)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, num_actions)
        
    def forward(self, x):
        embedded = self.action_embedding(x)
        out, (hidden, cell) = self.lstm(embedded)
        last_out = out[:, -1, :]
        return self.fc(last_out)

class BehaviorBiLSTM(nn.Module):
    def __init__(self, num_actions, embedding_dim=32, hidden_dim=64, num_layers=1):
        super(BehaviorBiLSTM, self).__init__()
        self.action_embedding = nn.Embedding(num_actions, embedding_dim)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, num_layers, batch_first=True, bidirectional=True)
        # Since it's bidirectional, the output hidden dimension is 2 * hidden_dim
        self.fc = nn.Linear(hidden_dim * 2, num_actions)
        
    def forward(self, x):
        embedded = self.action_embedding(x)
        out, (hidden, cell) = self.lstm(embedded)
        last_out = out[:, -1, :]
        return self.fc(last_out)
