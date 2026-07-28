"""
Модуль для сгущения псевдорегулярной сетки высот
Статическая модель поверхности рельефа
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D


class GridRefinement:
    """
    Класс для сгущения псевдорегулярной сетки высот
    с использованием билинейной интерполяции
    """
    
    def __init__(self, X, Y, Z):
        """
        Инициализация сетки
        
        Parameters:
        -----------
        X : array-like, shape (N_x+1,)
            Координаты границ ячеек по оси X
        Y : array-like, shape (N_y+1,)
            Координаты границ ячеек по оси Y
        Z : array-like, shape (N_x+1, N_y+1)
            Матрица высот в узлах сетки
        """
        self.X = np.array(X)
        self.Y = np.array(Y)
        self.Z = np.array(Z)
        
        # Проверка размерностей
        if self.Z.shape != (len(self.X), len(self.Y)):
            raise ValueError(f"Размерность Z должна быть ({len(self.X)}, {len(self.Y)})")
        
        self.N_x = len(self.X) - 1
        self.N_y = len(self.Y) - 1
    
    def bilinear_interpolation(self, x, y, i, j):
        """
        Билинейная интерполяция внутри ячейки [X_i, X_{i+1}] x [Y_j, Y_{j+1}]
        
        Parameters:
        -----------
        x, y : float
            Координаты точки для интерполяции
        i, j : int
            Индексы ячейки
        
        Returns:
        --------
        float
            Интерполированное значение высоты
        """
        # Значения в углах ячейки
        z_00 = self.Z[i, j]      # левый нижний
        z_10 = self.Z[i+1, j]    # правый нижний
        z_01 = self.Z[i, j+1]    # левый верхний
        z_11 = self.Z[i+1, j+1]  # правый верхний
        
        # Нормированные координаты
        dx = self.X[i+1] - self.X[i]
        dy = self.Y[j+1] - self.Y[j]
        
        if dx == 0 or dy == 0:
            return z_00
        
        u = (x - self.X[i]) / dx
        v = (y - self.Y[j]) / dy
        
        # Билинейная интерполяция
        z = (1 - u) * (1 - v) * z_00 + \
            u * (1 - v) * z_10 + \
            (1 - u) * v * z_01 + \
            u * v * z_11
        
        return z
    
    def find_cell(self, x, y):
        """
        Найти индексы ячейки, содержащей точку (x, y)
        
        Parameters:
        -----------
        x, y : float
            Координаты точки
        
        Returns:
        --------
        tuple (i, j) или None
            Индексы ячейки или None, если точка вне области
        """
        # Найти индексы для X
        i = None
        for idx in range(self.N_x):
            if self.X[idx] <= x <= self.X[idx+1]:
                i = idx
                break
        
        # Найти индексы для Y
        j = None
        for idx in range(self.N_y):
            if self.Y[idx] <= y <= self.Y[idx+1]:
                j = idx
                break
        
        if i is None or j is None:
            return None
        
        return (i, j)
    
    def refine_grid(self, k):
        """
        Сгущение сетки с коэффициентом k
        
        Parameters:
        -----------
        k : int
            Коэффициент сгущения (количество узлов на исходную ячейку)
        
        Returns:
        --------
        tuple (X_new, Y_new, Z_new)
            Новая сгущенная сетка и матрица высот
        """
        # Генерация новой сетки
        X_new_list = []
        Y_new_list = []
        
        # Генерируем узлы по X
        for i in range(self.N_x):
            x_start = self.X[i]
            x_end = self.X[i+1]
            dx = (x_end - x_start) / k
            x_nodes = [x_start + m * dx for m in range(k)]
            X_new_list.extend(x_nodes)
        # Добавляем последний узел
        X_new_list.append(self.X[-1])
        X_new = np.array(X_new_list)
        
        # Генерируем узлы по Y
        for j in range(self.N_y):
            y_start = self.Y[j]
            y_end = self.Y[j+1]
            dy = (y_end - y_start) / k
            y_nodes = [y_start + n * dy for n in range(k)]
            Y_new_list.extend(y_nodes)
        # Добавляем последний узел
        Y_new_list.append(self.Y[-1])
        Y_new = np.array(Y_new_list)
        
        # Вычисление высот на новой сетке
        Z_new = np.zeros((len(X_new), len(Y_new)))
        
        for i_new, x in enumerate(X_new):
            for j_new, y in enumerate(Y_new):
                # Найти исходную ячейку
                cell = self.find_cell(x, y)
                if cell is not None:
                    i, j = cell
                    Z_new[i_new, j_new] = self.bilinear_interpolation(x, y, i, j)
                else:
                    # Если точка вне области, используем ближайшее значение
                    Z_new[i_new, j_new] = self.Z[0, 0]
        
        return X_new, Y_new, Z_new
    
    def generate_test_grid(self, N_x=5, N_y=5, x_min=0, x_max=10, y_min=0, y_max=10):
        """
        Генерация тестовой псевдорегулярной сетки с заданными параметрами
        
        Parameters:
        -----------
        N_x, N_y : int
            Количество ячеек по осям
        x_min, x_max, y_min, y_max : float
            Границы области
        
        Returns:
        --------
        tuple (X, Y, Z)
            Сгенерированная сетка и матрица высот
        """
        # Генерация псевдорегулярной сетки (с небольшими отклонениями)
        np.random.seed(42)
        
        # X координаты с небольшими случайными отклонениями
        X_base = np.linspace(x_min, x_max, N_x + 1)
        X_noise = np.random.normal(0, 0.1 * (x_max - x_min) / N_x, N_x + 1)
        X_noise[0] = 0
        X_noise[-1] = 0
        X = X_base + X_noise
        X = np.sort(X)  # Сортируем для сохранения порядка
        
        # Y координаты с небольшими случайными отклонениями
        Y_base = np.linspace(y_min, y_max, N_y + 1)
        Y_noise = np.random.normal(0, 0.1 * (y_max - y_min) / N_y, N_y + 1)
        Y_noise[0] = 0
        Y_noise[-1] = 0
        Y = Y_base + Y_noise
        Y = np.sort(Y)  # Сортируем для сохранения порядка
        
        # Генерация матрицы высот (например, холмистая поверхность)
        X_grid, Y_grid = np.meshgrid(X, Y, indexing='ij')
        Z = 5 + 3 * np.sin(0.5 * X_grid) * np.cos(0.5 * Y_grid) + \
            2 * np.sin(0.2 * X_grid + 0.3 * Y_grid)
        
        # Обновляем внутренние данные
        self.X = X
        self.Y = Y
        self.Z = Z
        self.N_x = N_x
        self.N_y = N_y
        
        return X, Y, Z


def visualize_grids(X_orig, Y_orig, Z_orig, X_ref, Y_ref, Z_ref, k):
    """
    Визуализация исходной и сгущенной сеток
    
    Parameters:
    -----------
    X_orig, Y_orig, Z_orig : arrays
        Исходная сетка
    X_ref, Y_ref, Z_ref : arrays
        Сгущенная сетка
    k : int
        Коэффициент сгущения
    """
    fig = plt.figure(figsize=(16, 6))
    
    # 3D визуализация исходной сетки
    ax1 = fig.add_subplot(131, projection='3d')
    X_grid_orig, Y_grid_orig = np.meshgrid(X_orig, Y_orig, indexing='ij')
    surf1 = ax1.plot_surface(X_grid_orig, Y_grid_orig, Z_orig, 
                             cmap=cm.terrain, alpha=0.8, linewidth=0.5, 
                             antialiased=True)
    ax1.set_xlabel('X (м)', fontsize=10)
    ax1.set_ylabel('Y (м)', fontsize=10)
    ax1.set_zlabel('Высота (м)', fontsize=10)
    ax1.set_title(f'Исходная сетка\n({len(X_orig)-1}x{len(Y_orig)-1} ячеек)', 
                  fontsize=11, fontweight='bold')
    plt.colorbar(surf1, ax=ax1, shrink=0.5, aspect=20)
    
    # 3D визуализация сгущенной сетки
    ax2 = fig.add_subplot(132, projection='3d')
    X_grid_ref, Y_grid_ref = np.meshgrid(X_ref, Y_ref, indexing='ij')
    surf2 = ax2.plot_surface(X_grid_ref, Y_grid_ref, Z_ref, 
                            cmap=cm.terrain, alpha=0.8, linewidth=0.1, 
                            antialiased=True)
    ax2.set_xlabel('X (м)', fontsize=10)
    ax2.set_ylabel('Y (м)', fontsize=10)
    ax2.set_zlabel('Высота (м)', fontsize=10)
    ax2.set_title(f'Сгущенная сетка (k={k})\n({len(X_ref)-1}x{len(Y_ref)-1} ячеек)', 
                  fontsize=11, fontweight='bold')
    plt.colorbar(surf2, ax=ax2, shrink=0.5, aspect=20)
    
    # 2D контурная карта сравнения
    ax3 = fig.add_subplot(133)
    contour1 = ax3.contour(X_grid_orig, Y_grid_orig, Z_orig, 
                          levels=10, colors='blue', linestyles='--', 
                          linewidths=1.5, alpha=0.6, label='Исходная')
    contour2 = ax3.contour(X_grid_ref, Y_grid_ref, Z_ref, 
                          levels=20, colors='red', linestyles='-', 
                          linewidths=1, alpha=0.8, label=f'Сгущенная (k={k})')
    ax3.set_xlabel('X (м)', fontsize=10)
    ax3.set_ylabel('Y (м)', fontsize=10)
    ax3.set_title('Сравнение контурных карт', fontsize=11, fontweight='bold')
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.set_aspect('equal')
    
    plt.tight_layout()
    return fig


if __name__ == "__main__":
    # Создание тестовой сетки
    grid = GridRefinement([], [], np.array([[0]]))
    X_orig, Y_orig, Z_orig = grid.generate_test_grid(N_x=5, N_y=5, 
                                                     x_min=0, x_max=10, 
                                                     y_min=0, y_max=10)
    
    print("Исходная сетка:")
    print(f"  Размерность: {len(X_orig)-1} x {len(Y_orig)-1} ячеек")
    print(f"  Узлов: {len(X_orig)} x {len(Y_orig)}")
    print(f"  X: {X_orig}")
    print(f"  Y: {Y_orig}")
    print(f"  Z min/max: {Z_orig.min():.2f} / {Z_orig.max():.2f}")
    
    # Сгущение сетки
    k = 4  # Коэффициент сгущения
    X_ref, Y_ref, Z_ref = grid.refine_grid(k)
    
    print(f"\nСгущенная сетка (k={k}):")
    print(f"  Размерность: {len(X_ref)-1} x {len(Y_ref)-1} ячеек")
    print(f"  Узлов: {len(X_ref)} x {len(Y_ref)}")
    print(f"  Z min/max: {Z_ref.min():.2f} / {Z_ref.max():.2f}")
    
    # Визуализация
    fig = visualize_grids(X_orig, Y_orig, Z_orig, X_ref, Y_ref, Z_ref, k)
    plt.savefig('grid_refinement.png', dpi=300, bbox_inches='tight')
    print("\nГрафик сохранен в файл 'grid_refinement.png'")
    plt.show()

