import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from sklearn.metrics import accuracy_score, f1_score
import matplotlib.pyplot as plt
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from training.preprocess import load_and_preprocess
from models.sequence_models import BehaviorRNN, BehaviorLSTM, BehaviorBiLSTM


def train_model(model, train_loader, test_loader, criterion, optimizer, num_epochs=10):
    train_losses = []
    val_accuracies = []
    val_f1s = []
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    
    print(f"Training {model.__class__.__name__} on {device}")
    
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        
        for sequences, targets in train_loader:
            sequences, targets = sequences.to(device), targets.to(device)
            
            optimizer.zero_grad()
            outputs = model(sequences)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * sequences.size(0)
            
        epoch_loss = running_loss / len(train_loader.dataset)
        train_losses.append(epoch_loss)
        
        # Validation
        model.eval()
        all_preds = []
        all_targets = []
        with torch.no_grad():
            for sequences, targets in test_loader:
                sequences, targets = sequences.to(device), targets.to(device)
                outputs = model(sequences)
                _, preds = torch.max(outputs, 1)
                
                all_preds.extend(preds.cpu().numpy())
                all_targets.extend(targets.cpu().numpy())
                
        acc = accuracy_score(all_targets, all_preds)
        f1 = f1_score(all_targets, all_preds, average='weighted')
        
        val_accuracies.append(acc)
        val_f1s.append(f1)
        
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{num_epochs} - Loss: {epoch_loss:.4f} - Val Acc: {acc:.4f} - Val F1: {f1:.4f}")
            
    return train_losses, val_accuracies, val_f1s, acc, f1


def plot_metrics(history, model_names, save_path):
    epochs = range(1, len(history[model_names[0]]['loss']) + 1)
    
    plt.figure(figsize=(12, 4))
    
    # Loss plot
    plt.subplot(1, 2, 1)
    for name in model_names:
        plt.plot(epochs, history[name]['loss'], label=name)
    plt.title('Training Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    
    # Accuracy plot
    plt.subplot(1, 2, 2)
    for name in model_names:
        plt.plot(epochs, history[name]['acc'], label=name)
    plt.title('Validation Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()


def save_training_results(results, json_path, text_path):
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(results, json_file, indent=4)

    lines = [
        "Training Summary",
        f"Dataset: {results['dataset']['csv_path']}",
        f"Train samples: {results['dataset']['train_samples']}",
        f"Test samples: {results['dataset']['test_samples']}",
        f"Window size: {results['training']['window_size']}",
        f"Epochs: {results['training']['epochs']}",
        f"Batch size: {results['training']['batch_size']}",
        f"Device: {results['training']['device']}",
        "",
        f"Best model: {results['best_model']['name']}",
        f"Best accuracy: {results['best_model']['accuracy']:.4f}",
        f"Best weighted F1: {results['best_model']['f1']:.4f}",
        f"Model file: {results['artifacts']['best_model_path']}",
        f"Plot file: {results['artifacts']['metrics_plot_path']}",
        "",
        "Per-model results:",
    ]

    for model_name, metrics in results["models"].items():
        lines.extend(
            [
                f"- {model_name}: acc={metrics['final_accuracy']:.4f}, f1={metrics['final_f1']:.4f}",
                f"  last_loss={metrics['loss'][-1]:.4f}, epochs={len(metrics['loss'])}",
            ]
        )

    with open(text_path, "w", encoding="utf-8") as text_file:
        text_file.write("\n".join(lines))


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, 'data', 'data_user500.csv')
    models_dir = os.path.join(base_dir, 'models')
    training_dir = os.path.join(base_dir, 'training')
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(training_dir, exist_ok=True)

    window_size = 5
    batch_size = 32
    num_epochs = 20
    learning_rate = 0.001
    device = str(torch.device('cuda' if torch.cuda.is_available() else 'cpu'))

    train_ds, test_ds, num_actions, num_products, action_encoder = load_and_preprocess(
        csv_path,
        window_size=window_size,
    )

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)
    
    models_to_train = {
        'RNN': BehaviorRNN(num_actions=num_actions),
        'LSTM': BehaviorLSTM(num_actions=num_actions),
        'BiLSTM': BehaviorBiLSTM(num_actions=num_actions)
    }
    
    criterion = nn.CrossEntropyLoss()
    
    history = {}
    best_f1 = 0
    best_model_name = ""
    best_model_state = None
    best_acc = 0
    
    for name, model in models_to_train.items():
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        train_losses, val_accs, val_f1s, final_acc, final_f1 = train_model(
            model, train_loader, test_loader, criterion, optimizer, num_epochs
        )
        
        history[name] = {
            'loss': train_losses,
            'acc': val_accs,
            'f1': val_f1s,
            'final_accuracy': final_acc,
            'final_f1': final_f1,
        }
        
        if final_f1 > best_f1:
            best_f1 = final_f1
            best_acc = final_acc
            best_model_name = name
            best_model_state = model.state_dict()
            
    print(f"\nBest Model: {best_model_name} with F1-score: {best_f1:.4f}")
    
    # Save the best model
    best_model_path = os.path.join(models_dir, 'model_best.pt')
    torch.save({
        'model_state_dict': best_model_state,
        'model_name': best_model_name,
        'num_actions': num_actions,
        'encoder_classes': action_encoder.classes_,
        'window_size': window_size,
    }, best_model_path)
    print(f"Saved best model to {best_model_path}")
    
    # Plot metrics
    plot_path = os.path.join(training_dir, 'training_metrics.png')
    plot_metrics(history, list(models_to_train.keys()), plot_path)
    print(f"Saved training plots to {plot_path}")

    results = {
        "dataset": {
            "csv_path": csv_path,
            "train_samples": len(train_ds),
            "test_samples": len(test_ds),
            "num_actions": num_actions,
            "num_products": num_products,
            "action_classes": action_encoder.classes_.tolist(),
        },
        "training": {
            "window_size": window_size,
            "batch_size": batch_size,
            "epochs": num_epochs,
            "learning_rate": learning_rate,
            "device": device,
        },
        "models": history,
        "best_model": {
            "name": best_model_name,
            "accuracy": best_acc,
            "f1": best_f1,
        },
        "artifacts": {
            "best_model_path": best_model_path,
            "metrics_plot_path": plot_path,
        },
    }

    results_json_path = os.path.join(training_dir, "training_results.json")
    results_text_path = os.path.join(training_dir, "training_summary.txt")
    save_training_results(results, results_json_path, results_text_path)
    print(f"Saved training results to {results_json_path}")
    print(f"Saved training summary to {results_text_path}")

if __name__ == "__main__":
    main()
