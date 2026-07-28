using Plots
using LinearAlgebra

plotly()

# Тестовые функции
function rosenbrock(x)
    return (1.0 - x[1])^2 + 100.0*(x[2] - x[1]^2)^2
end

function rastrigin(x)
    n = length(x)
    return 20 + sum(x[i]^2 - 10*cos(2*pi*x[i]) for i in 1:n)
end

function schwefel(x)
    n = length(x)
    return 418.9829*n - sum(x[i]*sin(sqrt(abs(x[i]))) for i in 1:n)
end

# Функция для создания начального симплекса
function create_initial_simplex(x0, n, alpha=1.0)
    # Создаем правильный симплекс с центром в x0
    # Для n-мерного пространства нужно n+1 точка
    simplex = [copy(x0)]
    
    # Используем стандартный способ создания правильного симплекса
    # Основан на правильном симплексе с единичной длиной ребра
    q = (sqrt(n+1) - 1) / (n * sqrt(2))
    p = q + 1 / sqrt(2)
    
    for i in 1:n
        x_new = copy(x0)
        for j in 1:n
            if j == i
                x_new[j] += alpha * p
            else
                x_new[j] += alpha * q
            end
        end
        push!(simplex, x_new)
    end
    
    return simplex
end

# Метод простого симплекса для R^n (не Нельдер-Мид!)
function simplex_method(f, x0, eps=1e-6, alpha=1.0, max_iterations=5000, verbose=false)
    n = length(x0)
    simplex = create_initial_simplex(x0, n, alpha)
    
    # Траектории для визуализации
    trajectory = [copy(x0)]  # Все точки симплекса
    all_simplexes = [copy(simplex)]  # Все симплексы для визуализации
    
    iteration = 0
    last_best_value = f(simplex[argmin([f(p) for p in simplex])])
    no_improvement_count = 0
    
    if verbose
        println("Начало оптимизации...")
    end
    
    while iteration < max_iterations
        iteration += 1
        
        if verbose && iteration % 100 == 0
            current_best = f(simplex[argmin([f(p) for p in simplex])])
            println("Итерация $iteration, лучшее значение: $current_best")
        end
        
        # Сортируем точки симплекса по значению функции (от лучшей к худшей)
        # Лучшая - минимальное значение, худшая - максимальное
        sorted_indices = sortperm([f(p) for p in simplex])
        simplex = simplex[sorted_indices]
        
        # Проверка на сходимость: размер симплекса
        centroid = sum(simplex[1:end-1]) / (length(simplex) - 1)  # Центр всех точек кроме худшей
        max_distance = maximum([norm(p - centroid) for p in simplex])
        
        # Проверка на улучшение функции
        current_best_value = f(simplex[1])
        if abs(current_best_value - last_best_value) < eps
            no_improvement_count += 1
            if no_improvement_count > 10
                break
            end
        else
            no_improvement_count = 0
            last_best_value = current_best_value
        end
        
        if max_distance < eps
            break
        end
        
        # Худшая точка - последняя в отсортированном списке
        x_worst = simplex[end]
        f_worst = f(x_worst)
        
        # Центр остальных точек (кроме худшей)
        centroid = sum(simplex[1:end-1]) / (length(simplex) - 1)
        
        # Отражение худшей точки через центр (коэффициент отражения = 1)
        x_reflected = centroid + (centroid - x_worst)
        f_reflected = f(x_reflected)
        
        if f_reflected < f_worst
            # Отражение лучше худшей точки - заменяем
            simplex[end] = x_reflected
            push!(trajectory, copy(x_reflected))
        else
            # Отражение не лучше - сжимаем симплекс (уменьшаем все точки к лучшей)
            x_best = simplex[1]
            for i in 2:length(simplex)
                simplex[i] = x_best + 0.5 * (simplex[i] - x_best)
            end
            push!(trajectory, copy(x_best))
        end
        
        # Сохраняем симплекс для визуализации
        push!(all_simplexes, copy(simplex))
    end
    
    # Добавляем финальный симплекс
    if length(all_simplexes) == 0 || all_simplexes[end] != simplex
        push!(all_simplexes, copy(simplex))
    end
    
    # Возвращаем лучшую точку
    best_index = argmin([f(p) for p in simplex])
    result = simplex[best_index]
    
    return result, trajectory, all_simplexes
end

# Функция для создания 3D визуализации (для 2D и 3D)
function plot_simplex_3d(f, x0, result, trajectory, all_simplexes, title_str, x_range, y_range, n)
    if n == 2
        # 2D случай: рисуем треугольники
        x_grid = range(x_range[1], x_range[2], length=100)
        y_grid = range(y_range[1], y_range[2], length=100)
        X = repeat(reshape(x_grid, 1, :), length(y_grid), 1)
        Y = repeat(y_grid, 1, length(x_grid))
        Z = map((a,b) -> f([a,b]), X, Y)
        
        plt = surface(x_grid, y_grid, Z, color=:thermal, alpha=0.5, legend=true)
        
        # Рисуем треугольники симплексов
        colors = [:red, :green, :blue, :orange, :purple, :yellow, :cyan, :magenta]
        for (idx, simplex) in enumerate(all_simplexes)
            if length(simplex) >= 3
                color = colors[(idx-1) % length(colors) + 1]
                # Треугольник из первых 3 точек
                x_coords = [simplex[1][1], simplex[2][1], simplex[3][1], simplex[1][1]]
                y_coords = [simplex[1][2], simplex[2][2], simplex[3][2], simplex[1][2]]
                z_coords = [f(simplex[1]), f(simplex[2]), f(simplex[3]), f(simplex[1])]
                plot!(plt, x_coords, y_coords, z_coords, linecolor=color, linewidth=1.5, 
                      label=(idx == 1 ? "Симплексы" : ""), alpha=0.6)
            end
        end
        
        # Траектория (прореживаем для производительности)
        if length(trajectory) > 1
            step_traj = max(1, length(trajectory) ÷ 500)  # Максимум 500 точек
            trajectory_filtered = trajectory[1:step_traj:end]
            scatter3d!(plt, 
                [p[1] for p in trajectory_filtered], 
                [p[2] for p in trajectory_filtered], 
                [f(p) for p in trajectory_filtered], 
                color=:green, 
                markersize=2,
                label="Траектория"
            )
        end
        
        # Начальная и конечная точки
        scatter3d!(plt, [x0[1]], [x0[2]], [f(x0)], color=:yellow, markersize=8, label="Старт")
        scatter3d!(plt, [result[1]], [result[2]], [f(result)], color=:purple, markersize=8, label="Финиш")
        
        title!(plt, title_str)
        xlabel!(plt, "x")
        ylabel!(plt, "y")
        zlabel!(plt, "f(x,y)")
        
    elseif n == 3
        # 3D случай: рисуем только траекторию и точки (без поверхности функции)
        plt = plot3d(legend=true)
        
        # Траектория (прореживаем)
        if length(trajectory) > 1
            step_traj = max(1, length(trajectory) ÷ 500)  # Максимум 500 точек
            trajectory_filtered = trajectory[1:step_traj:end]
            scatter3d!(plt, 
                [p[1] for p in trajectory_filtered], 
                [p[2] for p in trajectory_filtered], 
                [p[3] for p in trajectory_filtered], 
                color=:green, 
                markersize=3,
                label="Траектория"
            )
        end
        
        # Начальная и конечная точки
        scatter3d!(plt, [x0[1]], [x0[2]], [x0[3]], color=:yellow, markersize=8, label="Старт")
        scatter3d!(plt, [result[1]], [result[2]], [result[3]], color=:purple, markersize=8, label="Финиш")
        
        title!(plt, title_str)
        xlabel!(plt, "x₁")
        ylabel!(plt, "x₂")
        zlabel!(plt, "x₃")
    else
        # n > 3: только траектория в 3D проекции
        plt = plot3d(legend=true)
        
        if length(trajectory) > 1
            scatter3d!(plt, 
                [p[1] for p in trajectory], 
                [p[2] for p in trajectory], 
                [length(p) > 2 ? p[3] : 0.0 for p in trajectory], 
                color=:green, 
                markersize=4,
                label="Траектория (проекция)"
            )
        end
        
        scatter3d!(plt, [x0[1]], [x0[2]], [length(x0) > 2 ? x0[3] : 0.0], color=:yellow, markersize=8, label="Старт")
        scatter3d!(plt, [result[1]], [result[2]], [length(result) > 2 ? result[3] : 0.0], color=:purple, markersize=8, label="Финиш")
        
        title!(plt, title_str)
        xlabel!(plt, "x₁")
        ylabel!(plt, "x₂")
        zlabel!(plt, "x₃ (проекция)")
    end
    
    return plt
end

# Функция для создания 2D контурного графика (только для n=2)
function plot_simplex_2d(f, x0, result, trajectory, all_simplexes, title_str, x_range, y_range, n)
    if n != 2
        # Для n != 2 возвращаем пустой график или проекцию
        plt = plot(title=title_str * " (только для 2D)")
        return plt
    end
    
    x_grid = range(x_range[1], x_range[2], length=100)
    y_grid = range(y_range[1], y_range[2], length=100)
    X = repeat(reshape(x_grid, 1, :), length(y_grid), 1)
    Y = repeat(y_grid, 1, length(x_grid))
    Z = map((a,b) -> f([a,b]), X, Y)
    
    plt = contour(x_grid, y_grid, Z, 
        color=:thermal, 
        levels=20,
        xlabel="x₁", 
        ylabel="x₂",
        title=title_str,
        legend=:topleft
    )
    
    # Рисуем треугольники симплексов
    colors = [:red, :green, :blue, :orange, :purple, :yellow, :cyan, :magenta]
    for (idx, simplex) in enumerate(all_simplexes)
        if length(simplex) >= 3
            color = colors[(idx-1) % length(colors) + 1]
            x_coords = [simplex[1][1], simplex[2][1], simplex[3][1], simplex[1][1]]
            y_coords = [simplex[1][2], simplex[2][2], simplex[3][2], simplex[1][2]]
            plot!(plt, x_coords, y_coords, color=color, linewidth=1.5, 
                  label=(idx == 1 ? "Симплексы" : ""), alpha=0.7)
        end
    end
    
    # Траектория (прореживаем для производительности)
    if length(trajectory) > 0
        step_traj = max(1, length(trajectory) ÷ 500)  # Максимум 500 точек
        trajectory_filtered = trajectory[1:step_traj:end]
        scatter!(plt, 
            [p[1] for p in trajectory_filtered], 
            [p[2] for p in trajectory_filtered], 
            color=:green, 
            markersize=2,
            label="Траектория"
        )
    end
    
    # Начальная и конечная точки
    scatter!(plt, [x0[1]], [x0[2]], color=:yellow, markersize=8, label="Старт")
    scatter!(plt, [result[1]], [result[2]], color=:purple, markersize=8, label="Финиш")
    
    plot!(plt, colorbar=true)
    
    return plt
end

# Основная функция для тестирования
function test_simplex(f, f_name, x0, x_range, y_range, n, show_plots=true)
    println("\n" * "="^60)
    println("Тестирование функции: $f_name")
    println("Размерность: $n")
    println("Начальная точка: $x0")
    println("="^60)
    
    result, trajectory, all_simplexes = simplex_method(f, x0)
    
    println("Результат: $result")
    println("Значение функции: $(f(result))")
    println("Количество итераций: $(length(all_simplexes))")
    println("Количество точек траектории: $(length(trajectory))")
    
    # Создание графиков
    title_3d = "Метод простого симплекса - $f_name (3D, n=$n)"
    title_2d = "Метод простого симплекса - $f_name (2D, n=$n)"
    
    plt_3d = plot_simplex_3d(f, x0, result, trajectory, all_simplexes, title_3d, x_range, y_range, n)
    plt_2d = plot_simplex_2d(f, x0, result, trajectory, all_simplexes, title_2d, x_range, y_range, n)
    
    # Отображение графиков сразу после вывода текста
    if show_plots
        display(plt_3d)
        if n == 2
            display(plt_2d)
        end
    end
    
    return result, trajectory, plt_3d, plt_2d
end

# Запуск тестов
println("Метод простого симплекса: Тестирование на трёх функциях")

# Тест 1: Розенброк (2D)
println("\n=== Тест 1: Розенброк (n=2) ===")
x0_rosenbrock_2d = [-2.0, -2.0]
result_r1, traj_r1, plt_3d_r1, plt_2d_r1 = test_simplex(rosenbrock, "Розенброк", x0_rosenbrock_2d, (-2.0, 2.0), (-2.0, 2.0), 2)

# Тест 2: Растригин (2D)
println("\n=== Тест 2: Растригин (n=2) ===")
x0_rastrigin_2d = [0.5, 0.5]
result_r2, traj_r2, plt_3d_r2, plt_2d_r2 = test_simplex(rastrigin, "Растригин", x0_rastrigin_2d, (-5.0, 5.0), (-5.0, 5.0), 2)

# Тест 3: Швефель (2D)
println("\n=== Тест 3: Швефель (n=2) ===")
x0_schwefel_2d = [0.5, 0.5]
result_r3, traj_r3, plt_3d_r3, plt_2d_r3 = test_simplex(schwefel, "Швефель", x0_schwefel_2d, (-10.0, 10.0), (-10.0, 10.0), 2)

# Тест 4: Растригин (3D)
println("\n=== Тест 4: Растригин (n=3) ===")
x0_rastrigin_3d = [0.5, 0.5, 0.5]
result_r4, traj_r4, plt_3d_r4, plt_2d_r4 = test_simplex(rastrigin, "Растригин", x0_rastrigin_3d, (-5.0, 5.0), (-5.0, 5.0), 3)

