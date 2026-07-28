import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from grid_refinement import GridRefinement

plt.rcParams['figure.figsize'] = (16, 8)
plt.rcParams['font.size'] = 10

def analytical_function(x, y):
    r = np.sqrt(x**2 + y**2)
    return np.sin(r)

n = 10
k = n - 1
x_min, x_max = -3.0, 3.0
y_min, y_max = -3.0, 3.0

x_nodes = np.linspace(x_min, x_max, n)
y_nodes = np.linspace(y_min, y_max, n)
X_grid, Y_grid = np.meshgrid(x_nodes, y_nodes, indexing='ij')
Z_nodes = analytical_function(X_grid, Y_grid)

fig = plt.figure(figsize=(16, 6))
ax1 = fig.add_subplot(121, projection='3d')
surf = ax1.plot_surface(X_grid, Y_grid, Z_nodes, cmap=cm.viridis,
                        alpha=0.9, linewidth=0.3, antialiased=True)
ax1.set_xlabel('X')
ax1.set_ylabel('Y')
ax1.set_zlabel('Z')
ax1.set_title(f'Исходная сетка {n}x{n} узлов')
plt.colorbar(surf, ax=ax1, shrink=0.6, aspect=20)
ax2 = fig.add_subplot(122)
contour = ax2.contourf(X_grid, Y_grid, Z_nodes, levels=20, cmap=cm.viridis)
ax2.set_xlabel('X')
ax2.set_ylabel('Y')
ax2.set_title('Контурная карта исходной сетки')
ax2.set_aspect('equal')
plt.colorbar(contour, ax=ax2, shrink=0.8)
plt.tight_layout()
plt.show()

grid = GridRefinement(x_nodes.copy(), y_nodes.copy(), Z_nodes.copy())

x_midpoints = [(x_nodes[i] + x_nodes[i+1]) / 2.0 for i in range(k)]
y_midpoints = [(y_nodes[j] + y_nodes[j+1]) / 2.0 for j in range(k)]
x_midpoints = np.array(x_midpoints)
y_midpoints = np.array(y_midpoints)
X_mid_grid, Y_mid_grid = np.meshgrid(x_midpoints, y_midpoints, indexing='ij')

Z_midpoints_interp = np.zeros((k, k))
for i in range(k):
    for j in range(k):
        Z_midpoints_interp[i, j] = grid.delaunay_interpolation(
            X_mid_grid[i, j], Y_mid_grid[i, j])

Z_midpoints_exact = analytical_function(X_mid_grid, Y_mid_grid)

Z_nodes_exact = analytical_function(X_grid, Y_grid)
error_nodes = np.abs(Z_nodes - Z_nodes_exact)
mean_error_nodes = np.mean(error_nodes)
max_error_nodes = np.max(error_nodes)

error_midpoints = np.abs(Z_midpoints_interp - Z_midpoints_exact)
mean_error_midpoints = np.mean(error_midpoints)
max_error_midpoints = np.max(error_midpoints)
rms_error_midpoints = np.sqrt(np.mean(error_midpoints**2))

total_nodes = n * n
total_midpoints = k * k
total_points = total_nodes + total_midpoints
total_mean_error = (mean_error_nodes * total_nodes +
                    mean_error_midpoints * total_midpoints) / total_points

fig = plt.figure(figsize=(18, 12))
ax1 = fig.add_subplot(2, 3, 1)
im1 = ax1.contourf(X_mid_grid, Y_mid_grid, Z_midpoints_interp,
                    levels=20, cmap=cm.viridis)
ax1.set_xlabel('X')
ax1.set_ylabel('Y')
ax1.set_title(f'Интерполированные значения ({k}x{k})')
ax1.set_aspect('equal')
plt.colorbar(im1, ax=ax1, shrink=0.8)
ax2 = fig.add_subplot(2, 3, 2)
im2 = ax2.contourf(X_mid_grid, Y_mid_grid, Z_midpoints_exact,
                    levels=20, cmap=cm.viridis)
ax2.set_xlabel('X')
ax2.set_ylabel('Y')
ax2.set_title(f'Точные значения ({k}x{k})')
ax2.set_aspect('equal')
plt.colorbar(im2, ax=ax2, shrink=0.8)
ax3 = fig.add_subplot(2, 3, 3)
im3 = ax3.contourf(X_mid_grid, Y_mid_grid, error_midpoints,
                    levels=20, cmap=cm.Reds)
ax3.set_xlabel('X')
ax3.set_ylabel('Y')
ax3.set_title(f'Погрешность (макс: {max_error_midpoints:.6f})')
ax3.set_aspect('equal')
plt.colorbar(im3, ax=ax3, shrink=0.8)
ax4 = fig.add_subplot(2, 3, 4, projection='3d')
ax4.plot_surface(X_mid_grid, Y_mid_grid, Z_midpoints_interp,
                 cmap=cm.viridis, alpha=0.9, linewidth=0.3)
ax4.set_xlabel('X')
ax4.set_ylabel('Y')
ax4.set_zlabel('Z')
ax4.set_title('3D: Интерполированные')
ax5 = fig.add_subplot(2, 3, 5, projection='3d')
ax5.plot_surface(X_mid_grid, Y_mid_grid, Z_midpoints_exact,
                 cmap=cm.viridis, alpha=0.9, linewidth=0.3)
ax5.set_xlabel('X')
ax5.set_ylabel('Y')
ax5.set_zlabel('Z')
ax5.set_title('3D: Точные')
ax6 = fig.add_subplot(2, 3, 6)
diff = Z_midpoints_interp - Z_midpoints_exact
im6 = ax6.contourf(X_mid_grid, Y_mid_grid, diff,
                    levels=20, cmap=cm.RdYlBu_r)
ax6.set_xlabel('X')
ax6.set_ylabel('Y')
ax6.set_title(f'Разница (средняя: {np.mean(diff):.6f})')
ax6.set_aspect('equal')
plt.colorbar(im6, ax=ax6, shrink=0.8)
plt.tight_layout()
plt.show()

print("=" * 60)
print("СТАТИСТИКА ПОГРЕШНОСТЕЙ")
print("=" * 60)
print(f"\nУзловые точки ({n}x{n} = {total_nodes}):")
print(f"  MAE: {mean_error_nodes:.10f}")
print(f"  MAX: {max_error_nodes:.10f}")
print(f"\nСередины ячеек ({k}x{k} = {total_midpoints}):")
print(f"  MAE: {mean_error_midpoints:.8f}")
print(f"  MAX: {max_error_midpoints:.8f}")
print(f"  RMS: {rms_error_midpoints:.8f}")
print(f"\n{'='*60}")
print(f"ОБЩАЯ MAE ({total_points} точек): {total_mean_error:.8f}")
print(f"{'='*60}")
