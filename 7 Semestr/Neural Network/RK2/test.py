import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import os
import glob
import pandas as pd
import sys
from pathlib import Path


class ImageClassifier:
    """Класс для инициализации модели, загрузки, препроцессинга и обработки изображений"""
    
    def __init__(self, model_path='model.pth', num_classes=50, device=None):
        """
        Инициализация модели
        
        Args:
            model_path: путь к файлу модели
            num_classes: количество классов
            device: устройство для вычислений (cuda/cpu)
        """
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = device
        
        # Препроцессинг входного объекта (аналогично валидации)
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # Создание модели
        self.model = self._create_model(num_classes)
        
        # Загрузка весов модели
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
        
        print(f"Model loaded from {model_path}")
        print(f"Using device: {self.device}")
    
    def _create_model(self, num_classes):
        """Создает архитектуру модели EfficientNet-B3"""
        model = models.efficientnet_b3(weights=None)  # Не загружаем предобученные веса
        
        # Заменяем классификатор (должно соответствовать train.py)
        num_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(0.4),
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )
        
        return model
    
    def preprocess(self, image_path):
        """
        Препроцессинг входного изображения
        
        Args:
            image_path: путь к изображению
            
        Returns:
            preprocessed_image: тензор изображения
        """
        image = Image.open(image_path).convert('RGB')
        image_tensor = self.transform(image)
        # Добавляем batch dimension
        image_tensor = image_tensor.unsqueeze(0)
        return image_tensor
    
    def predict(self, image_path, use_tta=True):
        """
        Обработка изображения и предсказание класса
        
        Args:
            image_path: путь к изображению
            use_tta: использовать test-time augmentation для лучшей точности
            
        Returns:
            class_label: предсказанный класс
        """
        if use_tta:
            # Test-time augmentation: делаем предсказания на нескольких вариантах изображения
            image = Image.open(image_path).convert('RGB')
            
            # Базовое преобразование
            base_transform = transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            # Варианты для TTA
            tta_transforms = [
                base_transform,  # Оригинал
                transforms.Compose([transforms.RandomHorizontalFlip(p=1.0), base_transform]),  # Горизонтальный флип
            ]
            
            all_outputs = []
            for tta_transform in tta_transforms:
                image_tensor = tta_transform(image).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    outputs = self.model(image_tensor)
                    all_outputs.append(outputs)
            
            # Усредняем предсказания
            avg_outputs = torch.stack(all_outputs).mean(0)
            _, predicted = torch.max(avg_outputs, 1)
            class_label = predicted.item()
        else:
            # Препроцессинг
            image_tensor = self.preprocess(image_path)
            image_tensor = image_tensor.to(self.device)
            
            # Обработка объекта
            with torch.no_grad():
                outputs = self.model(image_tensor)
                _, predicted = torch.max(outputs, 1)
                class_label = predicted.item()
        
        return class_label


def main():
    """Основная функция для обработки тестовых данных"""
    if len(sys.argv) < 2:
        print("Usage: python test.py <path_to_test_directory>")
        sys.exit(1)
    
    test_dir = sys.argv[1]
    test_path = os.path.join(test_dir, 'test')
    
    if not os.path.exists(test_path):
        print(f"Error: Test directory {test_path} does not exist")
        sys.exit(1)
    
    # Поиск всех jpg файлов в тестовой директории
    test_images = glob.glob(os.path.join(test_path, '*.jpg'))
    
    if len(test_images) == 0:
        print(f"Warning: No .jpg files found in {test_path}")
    
    print(f"Found {len(test_images)} test images")
    
    # Инициализация модели
    # Ищем model.pth в директории скрипта
    script_dir = Path(__file__).parent
    model_path = script_dir / 'model.pth'
    
    if not model_path.exists():
        # Если не найден, пробуем в текущей директории
        model_path = Path('model.pth')
        if not model_path.exists():
            print(f"Error: model.pth not found in {script_dir} or current directory")
            sys.exit(1)
    
    classifier = ImageClassifier(model_path=str(model_path), num_classes=50)
    
    # Обработка всех изображений
    results = []
    for img_path in test_images:
        # Получаем только имя файла
        filename = os.path.basename(img_path)
        
        # Извлекаем число из имени файла (например, "2.jpg" -> 2)
        try:
            # Убираем расширение .jpg и преобразуем в число
            file_index = int(filename.replace('.jpg', ''))
        except ValueError:
            print(f"Warning: Could not extract index from filename {filename}, skipping")
            continue
        
        # Предсказание класса (отключаем TTA для экономии памяти)
        predicted_class = classifier.predict(img_path, use_tta=False)
        
        results.append({
            'index': file_index,
            'label': predicted_class
        })
    
    # Создание DataFrame и сохранение
    df_results = pd.DataFrame(results)
    # Сортируем по index (числовая сортировка)
    df_results = df_results.sort_values('index')
    
    # Проверяем, что все классы заполнены
    if df_results['label'].isna().any():
        print(f"Warning: Found {df_results['label'].isna().sum()} rows with empty class values!")
        # Удаляем строки с пустыми классами
        df_results = df_results.dropna(subset=['label'])
    
    # Сохраняем в директории скрипта
    output_path = script_dir / 'label_test.csv'
    
    # Удаляем старый файл, если он существует
    if output_path.exists():
        output_path.unlink()
    
    # Сохраняем новый файл
    df_results.to_csv(output_path, index=False)
    
    print(f"Results saved to {output_path}")
    print(f"Total predictions: {len(results)}")
    print(f"Columns: {df_results.columns.tolist()}")
    print(f"\nFirst 10 rows:")
    print(df_results.head(10).to_string(index=False))
    
    # Проверяем сохраненный файл
    verify_df = pd.read_csv(output_path)
    print(f"\nVerification - Columns in saved file: {verify_df.columns.tolist()}")
    print(f"Verification - Rows with empty class: {verify_df['label'].isna().sum()}")


if __name__ == '__main__':
    main()

