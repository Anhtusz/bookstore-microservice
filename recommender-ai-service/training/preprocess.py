import pandas as pd
import numpy as np
import torch
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import Dataset
import os


class BehaviorDataset(Dataset):
    def __init__(self, sequences, targets):
        self.sequences = torch.tensor(sequences, dtype=torch.long)
        self.targets = torch.tensor(targets, dtype=torch.long)

    def __len__(self):
        return len(self.targets)

    def __getitem__(self, idx):
        return self.sequences[idx], self.targets[idx]


def encode_categorical_features(df):
    user_encoder = LabelEncoder()
    product_encoder = LabelEncoder()
    action_encoder = LabelEncoder()

    encoded_df = df.copy()
    encoded_df["user_encoded"] = user_encoder.fit_transform(encoded_df["user_id"])
    encoded_df["product_encoded"] = product_encoder.fit_transform(encoded_df["product_id"])
    encoded_df["action_encoded"] = action_encoder.fit_transform(encoded_df["action"])

    return encoded_df, user_encoder, product_encoder, action_encoder


def create_behavior_sequences(encoded_df, window_size):
    sequences = []
    targets = []

    print(f"Creating sequences with window size {window_size}...")
    for _, group in encoded_df.groupby("user_id"):
        user_actions = group["action_encoded"].to_numpy()

        if len(user_actions) <= window_size:
            continue

        for i in range(len(user_actions) - window_size):
            sequences.append(user_actions[i : i + window_size])
            targets.append(user_actions[i + window_size])

    return np.array(sequences), np.array(targets)


def load_and_preprocess(csv_path, window_size=5, test_split=0.2, random_state=42):
    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by=["user_id", "timestamp", "product_id"]).reset_index(drop=True)

    encoded_df, user_encoder, product_encoder, action_encoder = encode_categorical_features(df)

    action_mapping = dict(
        zip(action_encoder.classes_, action_encoder.transform(action_encoder.classes_))
    )
    print(f"Action encoding: {action_mapping}")
    print(f"Encoded users: {len(user_encoder.classes_)}")
    print(f"Encoded products: {len(product_encoder.classes_)}")

    sequences, targets = create_behavior_sequences(encoded_df, window_size=window_size)

    if len(sequences) == 0:
        raise ValueError("No sequences were created. Reduce the window size or inspect the source data.")

    rng = np.random.default_rng(random_state)
    indices = rng.permutation(len(sequences))
    test_size = max(1, int(len(sequences) * test_split))

    test_idx = indices[:test_size]
    train_idx = indices[test_size:]

    if len(train_idx) == 0:
        raise ValueError("Train split is empty. Increase the dataset size or reduce test_split.")

    train_seq, test_seq = sequences[train_idx], sequences[test_idx]
    train_target, test_target = targets[train_idx], targets[test_idx]

    train_dataset = BehaviorDataset(train_seq, train_target)
    test_dataset = BehaviorDataset(test_seq, test_target)

    load_and_preprocess.last_encoded_df = encoded_df
    load_and_preprocess.last_encoders = {
        "user_encoder": user_encoder,
        "product_encoder": product_encoder,
        "action_encoder": action_encoder,
    }

    return (
        train_dataset,
        test_dataset,
        len(action_encoder.classes_),
        len(product_encoder.classes_),
        action_encoder,
    )

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    csv_path = os.path.join(data_dir, "data_user500.csv")
    encoded_csv_path = os.path.join(data_dir, "data_user500_encoded.csv")

    train_ds, test_ds, n_act, n_prod, enc = load_and_preprocess(csv_path)
    load_and_preprocess.last_encoded_df.to_csv(encoded_csv_path, index=False)

    print(f"Train samples: {len(train_ds)}, Test samples: {len(test_ds)}")
    print(f"Num Actions: {n_act}, Num Products: {n_prod}")
    print(f"Encoded dataset saved to {encoded_csv_path}")
