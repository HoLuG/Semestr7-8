import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
import numpy as np
from tqdm import tqdm
from torch.cuda.amp import autocast, GradScaler

# Гиперпараметры
BATCH_SIZE = 16  # Уменьшено для GPU с ограниченной памятью
LEARNING_RATE = 0.001
NUM_EPOCHS = 60
NUM_CLASSES = 50
IMG_SIZE = 224
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
LABEL_SMOOTHING = 0.1  # Label smoothing для лучшей обобщающей способности

# Data augmentation для обучения (более агрессивная для лучшей обобщающей способности)
train_transform = transforms.Compose([
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.3),
    transforms.RandomRotation(20),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.15),
    transforms.RandomAffine(degrees=0, translate=(0.15, 0.15), scale=(0.85, 1.15)),
    transforms.RandomPerspective(distortion_scale=0.2, p=0.3),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    transforms.RandomErasing(p=0.2, scale=(0.02, 0.33))
])

# Препроцессинг для валидации
val_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


class ImageDataset(Dataset):
    def __init__(self, dataframe, data_dir, transform=None):
        self.dataframe = dataframe
        self.data_dir = data_dir
        self.transform = transform
    
    def __len__(self):
        return len(self.dataframe)
    
    def __getitem__(self, idx):
        img_name = self.dataframe.iloc[idx]['filenames']
        label = self.dataframe.iloc[idx]['label']
        
        img_path = os.path.join(self.data_dir, img_name)
        image = Image.open(img_path).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
        
        return image, label


def create_model(num_classes=50):
    """Создает модель EfficientNet-B3 с предобученными весами (оптимальный баланс точности и памяти)"""
    # Используем EfficientNet-B3 для баланса между точностью и использованием памяти
    model = models.efficientnet_b3(weights='EfficientNet_B3_Weights.DEFAULT')
    
    # Заменяем классификатор с улучшенной структурой
    num_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.4),
        nn.Linear(num_features, 512),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(512, num_classes)
    )
    
    return model


def train_epoch(model, dataloader, criterion, optimizer, scheduler, device, scaler=None):
    model.train()
    running_loss = 0.0
    all_preds = []
    all_labels = []
    
    for images, labels in tqdm(dataloader, desc='Training'):
        images = images.to(device)
        labels = labels.to(device)
        
        optimizer.zero_grad()
        
        # Mixed precision training для экономии памяти
        if scaler is not None:
            with autocast():
                outputs = model(images)
                loss = criterion(outputs, labels)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
        
        # Обновление learning rate на каждом батче для OneCycleLR
        scheduler.step()
        
        running_loss += loss.item()
        _, preds = torch.max(outputs, 1)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
    
    epoch_loss = running_loss / len(dataloader)
    epoch_f1 = f1_score(all_labels, all_preds, average='weighted')
    
    return epoch_loss, epoch_f1


def validate(model, dataloader, criterion, device):
    model.eval()
    running_loss = 0.0
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for images, labels in tqdm(dataloader, desc='Validating'):
            images = images.to(device)
            labels = labels.to(device)
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            running_loss += loss.item()
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    epoch_loss = running_loss / len(dataloader)
    epoch_f1 = f1_score(all_labels, all_preds, average='weighted')
    
    return epoch_loss, epoch_f1


def main():
    print(f"Using device: {DEVICE}")
    
    # Очистка кеша CUDA перед началом
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    # Загрузка данных
    print("Loading data...")
    df = pd.read_csv('labels.csv')
    print(f"Total samples: {len(df)}")
    print(f"Number of classes: {df['label'].nunique()}")
    
    # Разделение на train и validation
    train_df, val_df = train_test_split(
        df, 
        test_size=0.2, 
        random_state=42, 
        stratify=df['label']
    )
    
    print(f"Train samples: {len(train_df)}")
    print(f"Validation samples: {len(val_df)}")
    
    # Создание датасетов
    train_dataset = ImageDataset(train_df, 'data', transform=train_transform)
    val_dataset = ImageDataset(val_df, 'data', transform=val_transform)
    
    train_loader = DataLoader(
        train_dataset, 
        batch_size=BATCH_SIZE, 
        shuffle=True, 
        num_workers=2,  # Уменьшено для экономии памяти
        pin_memory=True if torch.cuda.is_available() else False
    )
    val_loader = DataLoader(
        val_dataset, 
        batch_size=BATCH_SIZE, 
        shuffle=False, 
        num_workers=2,  # Уменьшено для экономии памяти
        pin_memory=True if torch.cuda.is_available() else False
    )
    
    # Создание модели
    print("Creating model...")
    model = create_model(NUM_CLASSES)
    model = model.to(DEVICE)
    
    # Очистка кеша после загрузки модели
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    # Loss с label smoothing для лучшей обобщающей способности
    criterion = nn.CrossEntropyLoss(label_smoothing=LABEL_SMOOTHING)
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)
    
    # Learning rate scheduler с warmup
    # Используем OneCycleLR для более эффективного обучения
    scheduler = optim.lr_scheduler.OneCycleLR(
        optimizer,
        max_lr=LEARNING_RATE * 2,
        epochs=NUM_EPOCHS,
        steps_per_epoch=len(train_loader),
        pct_start=0.1,
        anneal_strategy='cos'
    )
    
    # Mixed precision training для экономии памяти GPU
    use_amp = torch.cuda.is_available()
    scaler = GradScaler() if use_amp else None
    if use_amp:
        print("Using mixed precision training (AMP) for memory efficiency")
    
    # Обучение
    best_f1 = 0.0
    best_model_state = None
    
    print("Starting training...")
    for epoch in range(NUM_EPOCHS):
        print(f"\nEpoch {epoch+1}/{NUM_EPOCHS}")
        print("-" * 50)
        
        # Обучение
        train_loss, train_f1 = train_epoch(model, train_loader, criterion, optimizer, scheduler, DEVICE, scaler)
        
        # Валидация
        val_loss, val_f1 = validate(model, val_loader, criterion, DEVICE)
        
        # Обновление learning rate (OneCycleLR обновляется на каждом батче)
        # Здесь не нужно вызывать step(), так как он вызывается в цикле обучения
        
        print(f"Train Loss: {train_loss:.4f}, Train F1: {train_f1:.4f}")
        print(f"Val Loss: {val_loss:.4f}, Val F1: {val_f1:.4f}")
        print(f"Learning Rate: {scheduler.get_last_lr()[0]:.6f}")
        
        # Сохранение лучшей модели
        if val_f1 > best_f1:
            best_f1 = val_f1
            best_model_state = model.state_dict().copy()
            print(f"New best F1 score: {best_f1:.4f}")
    
    # Загрузка лучшей модели
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
        print(f"\nBest validation F1 score: {best_f1:.4f}")
    
    # Сохранение модели
    print("Saving model...")
    torch.save(model.state_dict(), 'model.pth')
    print("Model saved to model.pth")
    
    # Финальная оценка на валидации
    print("\nFinal validation:")
    val_loss, val_f1 = validate(model, val_loader, criterion, DEVICE)
    print(f"Final Val F1: {val_f1:.4f}")


if __name__ == '__main__':
    main()

