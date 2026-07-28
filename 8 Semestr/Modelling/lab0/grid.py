import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from scipy.spatial import Delaunay
from scipy.interpolate import LinearNDInterpolator


class GridRefinement:
    def __init__(self, X=None, Y=None, Z=None):
        if X is None:
            X = []
        if Y is None:
            Y = []
        if Z is None:
            Z = np.array([[0]])
            
        self.X = np.array(X)
        self.Y = np.array(Y)
        self.Z = np.array(Z)
        

        if len(self.X) > 0 and len(self.Y) > 0:
            if self.Z.shape != (len(self.X), len(self.Y)):
                raise ValueError(f"Размерность Z должна быть ({len(self.X)}, {len(self.Y)}), получено {self.Z.shape}")
        
        self.N_x = max(0, len(self.X) - 1)
        self.N_y = max(0, len(self.Y) - 1)

        self.triangulation = None
        self.interpolator = None
    
    def _build_triangulation(self):
        if self.triangulation is not None:
            return
        
        if len(self.X) == 0 or len(self.Y) == 0:
            return
        
        points = []
        values = []
        
        for i in range(len(self.X)):
            for j in range(len(self.Y)):
                x = self.X[i]
                y = self.Y[j]
                z = self.Z[i, j]
                points.append([x, y])
                values.append(z)
        
        points = np.array(points)
        values = np.array(values)
        
        self.triangulation = Delaunay(points)
        
        self.interpolator = LinearNDInterpolator(self.triangulation, values)
    
    def delaunay_interpolation(self, x, y):
        if self.triangulation is None:
            self._build_triangulation()
        
        if self.interpolator is None:
            return self.Z[0, 0]
        
        z = self.interpolator(x, y)
        
        if np.isnan(z):
            points = np.array([[self.X[i], self.Y[j]] for i in range(len(self.X)) for j in range(len(self.Y))])
            dists = np.sqrt((points[:, 0] - x)**2 + (points[:, 1] - y)**2)
            nearest_idx = np.argmin(dists)
            i_nearest = nearest_idx // len(self.Y)
            j_nearest = nearest_idx % len(self.Y)
            return self.Z[i_nearest, j_nearest]
        
        return z
    
    def refine_grid_midpoints(self):
        X_new_list = []
        Y_new_list = []
        
        for i in range(len(self.X)):
            X_new_list.append(self.X[i])
            if i < len(self.X) - 1:
                x_mid = (self.X[i] + self.X[i+1]) / 2.0
                X_new_list.append(x_mid)
        X_new = np.array(sorted(set(X_new_list)))
        
        for j in range(len(self.Y)):
            Y_new_list.append(self.Y[j])
            if j < len(self.Y) - 1:
                y_mid = (self.Y[j] + self.Y[j+1]) / 2.0
                Y_new_list.append(y_mid)
        Y_new = np.array(sorted(set(Y_new_list)))
        
        Z_new = np.zeros((len(X_new), len(Y_new)))
        
        for i_new, x in enumerate(X_new):
            for j_new, y in enumerate(Y_new):
                is_original_x = np.any(np.abs(self.X - x) < 1e-10)
                is_original_y = np.any(np.abs(self.Y - y) < 1e-10)
                
                if is_original_x and is_original_y:
                    i_orig = np.where(np.abs(self.X - x) < 1e-10)[0][0]
                    j_orig = np.where(np.abs(self.Y - y) < 1e-10)[0][0]
                    Z_new[i_new, j_new] = self.Z[i_orig, j_orig]
                else:
                    Z_new[i_new, j_new] = self.delaunay_interpolation(x, y)
        
        return X_new, Y_new, Z_new
        """
        Сгущение сетки с коэффициентом k (старый метод для обратной совместимости)
        
        Parameters:
        -----------
        k : int
            Коэффициент сгущения (количество узлов на исходную ячейку)
        
        Returns:
        --------
        tuple (X_new, Y_new, Z_new)
            Новая сгущенная сетка и матрица высот
        """
        # Если k=2, используем метод середин
        if k == 2:
            return self.refine_grid_midpoints()
        
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
                # Интерполируем с помощью триангуляции Делоне
                Z_new[i_new, j_new] = self.delaunay_interpolation(x, y)
        
        return X_new, Y_new, Z_new
    
        """
        Адаптивное сгущение сетки на основе градиента высоты.
        Добавляет узлы в областях с большими изменениями высоты.
        
        Parameters:
        -----------
        threshold_factor : float
            Пороговый коэффициент для определения областей с большим градиентом
            (0.0 - 1.0, чем меньше, тем больше узлов будет добавлено)
        
        Returns:
        --------
        tuple (X_new, Y_new, Z_new)
            Новая сгущенная сетка и матрица высот
        """
        # Вычисляем градиенты на исходной сетке
        grad_x = np.zeros_like(self.Z)
        grad_y = np.zeros_like(self.Z)
        
        for i in range(self.N_x + 1):
            for j in range(self.N_y + 1):
                # Градиент по X
                if i < self.N_x:
                    dx = self.X[i+1] - self.X[i]
                    if dx > 1e-10:
                        grad_x[i, j] = (self.Z[i+1, j] - self.Z[i, j]) / dx
                # Градиент по Y
                if j < self.N_y:
                    dy = self.Y[j+1] - self.Y[j]
                    if dy > 1e-10:
                        grad_y[i, j] = (self.Z[i, j+1] - self.Z[i, j]) / dy
        
        # Вычисляем модуль градиента
        grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Порог для добавления узлов
        grad_threshold = np.percentile(grad_magnitude, (1 - threshold_factor) * 100)
        
        # Определяем, где добавлять узлы
        X_new_list = list(self.X)
        Y_new_list = list(self.Y)
        
        # Добавляем узлы по X в областях с большим градиентом
        for i in range(self.N_x):
            # Проверяем градиент в ячейке
            cell_grad = np.max(grad_magnitude[i:i+2, :])
            if cell_grad > grad_threshold:
                x_mid = (self.X[i] + self.X[i+1]) / 2.0
                if x_mid not in X_new_list:
                    X_new_list.append(x_mid)
        
        # Добавляем узлы по Y в областях с большим градиентом
        for j in range(self.N_y):
            # Проверяем градиент в ячейке
            cell_grad = np.max(grad_magnitude[:, j:j+2])
            if cell_grad > grad_threshold:
                y_mid = (self.Y[j] + self.Y[j+1]) / 2.0
                if y_mid not in Y_new_list:
                    Y_new_list.append(y_mid)
        
        X_new = np.array(sorted(set(X_new_list)))
        Y_new = np.array(sorted(set(Y_new_list)))
        
        # Вычисление высот на новой сетке
        Z_new = np.zeros((len(X_new), len(Y_new)))
        for i_new, x in enumerate(X_new):
            for j_new, y in enumerate(Y_new):
                is_original_x = np.any(np.abs(self.X - x) < 1e-10)
                is_original_y = np.any(np.abs(self.Y - y) < 1e-10)
                
                if is_original_x and is_original_y:
                    i_orig = np.where(np.abs(self.X - x) < 1e-10)[0][0]
                    j_orig = np.where(np.abs(self.Y - y) < 1e-10)[0][0]
                    Z_new[i_new, j_new] = self.Z[i_orig, j_orig]
                else:
                    Z_new[i_new, j_new] = self.delaunay_interpolation(x, y)
        
        return X_new, Y_new, Z_new
        """
        Адаптивное сгущение сетки на основе оценки ошибки интерполяции.
        Добавляет узлы в областях с наибольшей ошибкой.
        
        Parameters:
        -----------
        reference_func : callable, optional
            Референсная функция для вычисления точного значения (если известна)
            Если None, используется оценка ошибки на основе второй производной
        threshold_factor : float
            Пороговый коэффициент для определения областей с большой ошибкой
        
        Returns:
        --------
        tuple (X_new, Y_new, Z_new)
            Новая сгущенная сетка и матрица высот
        """
        # Оценка ошибки через вторую производную (лапласиан)
        error_estimate = np.zeros((self.N_x + 1, self.N_y + 1))
        
        for i in range(1, self.N_x):
            for j in range(1, self.N_y):
                # Вторая производная по X (конечные разности)
                if i > 0 and i < self.N_x:
                    dx1 = self.X[i] - self.X[i-1]
                    dx2 = self.X[i+1] - self.X[i]
                    if dx1 > 1e-10 and dx2 > 1e-10:
                        d2z_dx2 = 2 * ((self.Z[i+1, j] - self.Z[i, j]) / dx2 - 
                                      (self.Z[i, j] - self.Z[i-1, j]) / dx1) / (dx1 + dx2)
                    else:
                        d2z_dx2 = 0
                else:
                    d2z_dx2 = 0
                
                # Вторая производная по Y
                if j > 0 and j < self.N_y:
                    dy1 = self.Y[j] - self.Y[j-1]
                    dy2 = self.Y[j+1] - self.Y[j]
                    if dy1 > 1e-10 and dy2 > 1e-10:
                        d2z_dy2 = 2 * ((self.Z[i, j+1] - self.Z[i, j]) / dy2 - 
                                      (self.Z[i, j] - self.Z[i, j-1]) / dy1) / (dy1 + dy2)
                    else:
                        d2z_dy2 = 0
                else:
                    d2z_dy2 = 0
                
                # Оценка ошибки как модуль лапласиана
                error_estimate[i, j] = abs(d2z_dx2) + abs(d2z_dy2)
        
        # Порог для добавления узлов
        error_threshold = np.percentile(error_estimate[error_estimate > 0], 
                                       (1 - threshold_factor) * 100) if np.any(error_estimate > 0) else 0
        
        X_new_list = list(self.X)
        Y_new_list = list(self.Y)
        
        # Добавляем узлы по X в областях с большой ошибкой
        for i in range(self.N_x):
            cell_error = np.max(error_estimate[i:i+2, :])
            if cell_error > error_threshold:
                x_mid = (self.X[i] + self.X[i+1]) / 2.0
                if x_mid not in X_new_list:
                    X_new_list.append(x_mid)
        
        # Добавляем узлы по Y в областях с большой ошибкой
        for j in range(self.N_y):
            cell_error = np.max(error_estimate[:, j:j+2])
            if cell_error > error_threshold:
                y_mid = (self.Y[j] + self.Y[j+1]) / 2.0
                if y_mid not in Y_new_list:
                    Y_new_list.append(y_mid)
        
        X_new = np.array(sorted(set(X_new_list)))
        Y_new = np.array(sorted(set(Y_new_list)))
        
        # Вычисление высот на новой сетке
        Z_new = np.zeros((len(X_new), len(Y_new)))
        for i_new, x in enumerate(X_new):
            for j_new, y in enumerate(Y_new):
                is_original_x = np.any(np.abs(self.X - x) < 1e-10)
                is_original_y = np.any(np.abs(self.Y - y) < 1e-10)
                
                if is_original_x and is_original_y:
                    i_orig = np.where(np.abs(self.X - x) < 1e-10)[0][0]
                    j_orig = np.where(np.abs(self.Y - y) < 1e-10)[0][0]
                    Z_new[i_new, j_new] = self.Z[i_orig, j_orig]
                else:
                    Z_new[i_new, j_new] = self.delaunay_interpolation(x, y)
        
        return X_new, Y_new, Z_new
    
    def generate_test_grid(self, N_x=5, N_y=5, x_min=0, x_max=10, y_min=0, y_max=10, 
                          surface_type='hill'):
        np.random.seed(42)
        
        X_base = np.linspace(x_min, x_max, N_x + 1)
        X_noise = np.random.normal(0, 0.1 * (x_max - x_min) / N_x, N_x + 1)
        X_noise[0] = 0
        X_noise[-1] = 0
        X = X_base + X_noise
        X = np.sort(X)
        
        Y_base = np.linspace(y_min, y_max, N_y + 1)
        Y_noise = np.random.normal(0, 0.1 * (y_max - y_min) / N_y, N_y + 1)
        Y_noise[0] = 0
        Y_noise[-1] = 0
        Y = Y_base + Y_noise
        Y = np.sort(Y)
        
        X_grid, Y_grid = np.meshgrid(X, Y, indexing='ij')
        
        if surface_type == 'hill':
            Z = 5 + 3 * np.sin(0.5 * X_grid) * np.cos(0.5 * Y_grid) + \
                2 * np.sin(0.2 * X_grid + 0.3 * Y_grid)
        elif surface_type == 'gaussian':
            center_x, center_y = (x_min + x_max) / 2, (y_min + y_max) / 2
            Z = 10 * np.exp(-((X_grid - center_x)**2 + (Y_grid - center_y)**2) / 8)
        elif surface_type == 'parabolic':
            center_x, center_y = (x_min + x_max) / 2, (y_min + y_max) / 2
            Z = 10 - 0.5 * ((X_grid - center_x)**2 + (Y_grid - center_y)**2)
            Z = np.maximum(Z, 0)
        elif surface_type == 'sine':
            Z = 5 + 4 * np.sin(0.8 * X_grid) * np.sin(0.8 * Y_grid) + \
                2 * np.cos(1.5 * X_grid) * np.cos(1.5 * Y_grid)
        elif surface_type == 'ridge':
            Z = 5 + 4 * np.exp(-((X_grid - (x_min + x_max) / 2)**2) / 2) * \
                np.cos(0.5 * Y_grid)
        elif surface_type == 'valley':
            center_x = (x_min + x_max) / 2
            Z = 8 - 3 * np.exp(-((X_grid - center_x)**2) / 4) + \
                1.5 * np.sin(0.4 * Y_grid)
        else:
            Z = 5 + 3 * np.sin(0.5 * X_grid) * np.cos(0.5 * Y_grid)
        
        self.X = X
        self.Y = Y
        self.Z = Z
        self.N_x = N_x
        self.N_y = N_y
        
        return X, Y, Z


def visualize_grids(X_orig, Y_orig, Z_orig, X_ref, Y_ref, Z_ref, k):
    fig = plt.figure(figsize=(16, 6))
    
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
    grid = GridRefinement()
    X_orig, Y_orig, Z_orig = grid.generate_test_grid(N_x=20, N_y=20, 
                                                     x_min=0, x_max=10, 
                                                     y_min=0, y_max=10)
    
    print("Исходная сетка:")
    print(f"  Размерность: {len(X_orig)-1} x {len(Y_orig)-1} ячеек")
    print(f"  Узлов: {len(X_orig)} x {len(Y_orig)}")
    if len(X_orig) > 10:
        print(f"  X (примеры): {X_orig[1:6]} ... {X_orig[-2:]}")
        print(f"  Y (примеры): {Y_orig[1:6]} ... {Y_orig[-2:]}")
    else:
        print(f"  X: {X_orig}")
        print(f"  Y: {Y_orig}")
    print(f"  Z min/max: {Z_orig.min():.2f} / {Z_orig.max():.2f}")
    
    X_ref, Y_ref, Z_ref = grid.refine_grid_midpoints()
    
    print(f"\nСгущенная сетка (добавление середин):")
    print(f"  Размерность: {len(X_ref)-1} x {len(Y_ref)-1} ячеек")
    print(f"  Узлов: {len(X_ref)} x {len(Y_ref)}")
    if len(X_ref) > 10:
        print(f"  X (примеры): {X_ref[1:6]} ... {X_ref[-2:]}")
        print(f"  Y (примеры): {Y_ref[1:6]} ... {Y_ref[-2:]}")
    else:
        print(f"  X: {X_ref}")
        print(f"  Y: {Y_ref}")
    print(f"  Z min/max: {Z_ref.min():.2f} / {Z_ref.max():.2f}")
    
    # Визуализация
    fig = visualize_grids(X_orig, Y_orig, Z_orig, X_ref, Y_ref, Z_ref, k=2)
    plt.savefig('grid_refinement.png', dpi=300, bbox_inches='tight')
    print("\nГрафик сохранен в файл 'grid_refinement.png'")
    plt.show()

