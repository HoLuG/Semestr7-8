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

# Вариант А: Тупой метод - по 1 клетке, смотрим во все стороны
function hooke_jeeves_variant_a(f, x0, eps=1e-6, delta0=0.1)
    n = length(x0)
    delta = fill(delta0, n)
    x = copy(x0)
    
    # Траектории для визуализации
    trajectory = [copy(x)]  # Релаксационная последовательность (зелёные точки - убывание)
    search_points = [copy(x)]  # Точки поиска направления
    max_points = []  # Красные точки - где функция не убывает (максимум)
    trajectory_colors = [:green]  # Цвета точек траектории
    
    iteration = 0
    max_iterations = 10000
    
    while maximum(delta) > eps && iteration < max_iterations
        iteration += 1
        x_prev = copy(x)
        f_prev = f(x_prev)
        
        # Исследовательский поиск - смотрим во все стороны (по 1 клетке)
        x_new = copy(x)
        improved = false
        
        for i in 1:n
            # Пробуем +delta
            x_test = copy(x_new)
            x_test[i] += delta[i]
            f_test = f(x_test)
            push!(search_points, copy(x_test))  # Отмечаем все проверенные точки
            
            if f_test < f(x_new)
                x_new = x_test
                improved = true
            else
                # Пробуем -delta
                x_test = copy(x_new)
                x_test[i] -= delta[i]
                f_test = f(x_test)
                push!(search_points, copy(x_test))  # Отмечаем все проверенные точки
                
                if f_test < f(x_new)
                    x_new = x_test
                    improved = true
                end
            end
        end
        
        # Если функция убывает - добавляем в траекторию зелёным
        if f(x_new) < f_prev
            x = copy(x_new)
            push!(trajectory, copy(x))
            push!(trajectory_colors, :green)
        else
            # Функция не убывает - уменьшаем шаг
            push!(max_points, copy(x))
            delta = delta / 2.0
            
            # Если шаг стал слишком маленьким или функция не изменилась - останавливаемся
            if maximum(delta) < eps || abs(f(x) - f_prev) < eps
                break
            end
        end
    end
    
    return x, trajectory, search_points, max_points, trajectory_colors
end

# Вариант Б: Движемся вдоль направления пока функция убывает
function hooke_jeeves_variant_b(f, x0, eps=1e-6, delta0=0.1)
    n = length(x0)
    delta = fill(delta0, n)
    x = copy(x0)
    
    # Траектории для визуализации
    trajectory = [copy(x)]  # Релаксационная последовательность (зелёные точки - убывание)
    search_points = [copy(x)]  # Точки поиска направления
    max_points = []  # Красные точки - где функция не убывает
    trajectory_colors = [:green]  # Цвета точек траектории
    
    iteration = 0
    max_iterations = 10000
    
    while maximum(delta) > eps && iteration < max_iterations
        iteration += 1
        x_prev = copy(x)
        f_prev = f(x_prev)
        
        # Исследовательский поиск - находим направление
        x_exp, direction_search_points = exploratory_search(f, x, delta)
        append!(search_points, direction_search_points)
        
        # Если исследовательский поиск не дал улучшения - уменьшаем шаг
        if f(x_exp) >= f(x)
            push!(max_points, copy(x))
            delta = delta / 2.0
            continue
        end
        
        # Движемся вдоль направления пока функция убывает
        direction = x_exp - x
        step_size = norm(direction)
        
        if step_size > eps
            # Нормализуем направление
            direction_normalized = direction / step_size
            
            # Движемся вдоль направления с одинаковым шагом пока функция убывает
            x_current = copy(x_exp)
            f_current = f(x_current)
            improved = true
            
            while improved
                x_next = x_current + direction_normalized * step_size
                f_next = f(x_next)
                
                if f_next < f_current
                    x_current = x_next
                    f_current = f_next
                    push!(trajectory, copy(x_current))
                    push!(trajectory_colors, :green)
                else
                    # Функция перестала убывать - делаем откат назад
                    improved = false
                end
            end
            
            # Откат назад на половину шага от последней успешной точки
            x_rollback = x_current - direction_normalized * step_size / 2.0
            f_rollback = f(x_rollback)
            
            # Выбираем лучшую точку между откатом и текущей
            if f_rollback < f_current
                x = copy(x_rollback)
            else
                x = copy(x_current)
            end
            
            push!(trajectory, copy(x))
            push!(trajectory_colors, :green)
        else
            x = copy(x_exp)
            push!(trajectory, copy(x))
            push!(trajectory_colors, :green)
        end
        
        # Проверка на остановку
        if norm(x - x_prev) < eps || abs(f(x) - f_prev) < eps
            break
        end
    end
    
    return x, trajectory, search_points, max_points, trajectory_colors
end

# Вспомогательная функция для исследовательского поиска
function exploratory_search(f, x, delta)
    n = length(x)
    x_new = copy(x)
    direction_points = [copy(x)]  # Массив для хранения точек выбора направления

    for i in 1:n
        start_val = f(x_new)
        temp = x_new[i]
        x_new[i] = temp + delta[i]
        f_plus = f(x_new)

        if f_plus >= start_val
            x_new[i] = temp - delta[i]
            f_minus = f(x_new)
            if f_minus >= start_val
                x_new[i] = temp
            end
        end
        push!(direction_points, copy(x_new))
    end

    return x_new, direction_points
end

# Функция для создания 3D визуализации
function plot_optimization_3d(f, x0, result, trajectory, search_points, max_points, trajectory_colors, title_str, x_range, y_range)
    # Подготовка данных для 3D графика
    x_grid = range(x_range[1], x_range[2], length=100)
    y_grid = range(y_range[1], y_range[2], length=100)
    X = repeat(reshape(x_grid, 1, :), length(y_grid), 1)
    Y = repeat(y_grid, 1, length(x_grid))
    Z = map((a,b) -> f([a,b]), X, Y)
    
    # Создание 3D визуализации
    plt = surface(x_grid, y_grid, Z, color=:thermal, alpha=0.5, legend=true)
    
    # Рисуем траекторию с цветами (зелёные линии для убывания)
    if length(trajectory) > 1
        for i in 1:length(trajectory)-1
            color = trajectory_colors[i]
            plot!(plt, 
                [trajectory[i][1], trajectory[i+1][1]], 
                [trajectory[i][2], trajectory[i+1][2]], 
                [f(trajectory[i]), f(trajectory[i+1])], 
                linecolor=color, 
                linewidth=2,
                label=(i == 1 ? "Релаксационная последовательность" : "")
            )
        end
    end
    
    # Точки траектории (зелёные точки для убывания)
    if length(trajectory) > 0
        scatter3d!(plt, 
            [p[1] for p in trajectory], 
            [p[2] for p in trajectory], 
            [f(p) for p in trajectory], 
            color=:green, 
            markersize=4,
            label="Убывание"
        )
    end
    
    # Точки поиска направления (синие)
    if length(search_points) > 0
        scatter3d!(plt, 
            [p[1] for p in search_points], 
            [p[2] for p in search_points], 
            [f(p) for p in search_points], 
            color=:blue, 
            markersize=3,
            label="Поиск направления"
        )
    end
    
    # Красные точки - где функция не убывает
    if length(max_points) > 0
        scatter3d!(plt, 
            [p[1] for p in max_points], 
            [p[2] for p in max_points], 
            [f(p) for p in max_points], 
            color=:red, 
            markersize=5,
            label="Максимум"
        )
    end
    
    # Начальная и конечная точки
    scatter3d!(plt, [x0[1]], [x0[2]], [f(x0)], color=:yellow, markersize=8, label="Старт")
    scatter3d!(plt, [result[1]], [result[2]], [f(result)], color=:purple, markersize=8, label="Финиш")
    
    title!(plt, title_str)
    xlabel!(plt, "x")
    ylabel!(plt, "y")
    zlabel!(plt, "f(x,y)")
    
    return plt
end

# Функция для создания 2D контурного графика
function plot_optimization_2d(f, x0, result, trajectory, search_points, max_points, trajectory_colors, title_str, x_range, y_range)
    # Подготовка данных для контурного графика
    x_grid = range(x_range[1], x_range[2], length=100)
    y_grid = range(y_range[1], y_range[2], length=100)
    X = repeat(reshape(x_grid, 1, :), length(y_grid), 1)
    Y = repeat(y_grid, 1, length(x_grid))
    Z = map((a,b) -> f([a,b]), X, Y)
    
    # Создание контурного графика
    plt = contour(x_grid, y_grid, Z, 
        color=:thermal, 
        levels=20,
        xlabel="x₁", 
        ylabel="x₂",
        title=title_str,
        legend=:topleft
    )
    
    # Рисуем траекторию с цветами (зелёные линии для убывания)
    if length(trajectory) > 1
        for i in 1:length(trajectory)-1
            color = trajectory_colors[i]
            plot!(plt, 
                [trajectory[i][1], trajectory[i+1][1]], 
                [trajectory[i][2], trajectory[i+1][2]], 
                color=color, 
                linewidth=2,
                label=(i == 1 ? "Релаксационная последовательность" : "")
            )
        end
    end
    
    # Точки траектории (зелёные точки для убывания)
    if length(trajectory) > 0
        scatter!(plt, 
            [p[1] for p in trajectory], 
            [p[2] for p in trajectory], 
            color=:green, 
            markersize=4,
            label="Убывание"
        )
    end
    
    # Точки поиска направления (синие)
    if length(search_points) > 0
        scatter!(plt, 
            [p[1] for p in search_points], 
            [p[2] for p in search_points], 
            color=:blue, 
            markersize=3,
            label="Поиск направления"
        )
    end
    
    # Красные точки - где функция не убывает
    if length(max_points) > 0
        scatter!(plt, 
            [p[1] for p in max_points], 
            [p[2] for p in max_points], 
            color=:red, 
            markersize=5,
            label="Максимум"
        )
    end
    
    # Начальная и конечная точки
    scatter!(plt, 
        [x0[1], result[1]], 
        [x0[2], result[2]], 
        color=[:yellow :purple],
        markersize=8,
        label=["Старт" "Финиш"]
    )
    
    plot!(plt, colorbar=true)
    
    return plt
end

# Основная функция для тестирования
function test_function(f, f_name, x0, x_range, y_range, variant="a")
    println("\n" * "="^60)
    println("Тестирование функции: $f_name")
    println("Начальная точка: $x0")
    println("Вариант: $variant")
    println("="^60)
    
    if variant == "a"
        result, trajectory, search_points, max_points, trajectory_colors = hooke_jeeves_variant_a(f, x0)
    else
        result, trajectory, search_points, max_points, trajectory_colors = hooke_jeeves_variant_b(f, x0)
    end
    
    println("Результат: $result")
    println("Значение функции: $(f(result))")
    println("Количество итераций: $(length(trajectory))")
    println("Количество точек поиска: $(length(search_points))")
    println("Количество точек максимума: $(length(max_points))")
    
    # Создание графиков
    title_3d = "Метод Хука-Дживса (Вариант $variant) - $f_name (3D)"
    title_2d = "Метод Хука-Дживса (Вариант $variant) - $f_name (2D)"
    
    plt_3d = plot_optimization_3d(f, x0, result, trajectory, search_points, max_points, trajectory_colors, title_3d, x_range, y_range)
    plt_2d = plot_optimization_2d(f, x0, result, trajectory, search_points, max_points, trajectory_colors, title_2d, x_range, y_range)
    
    return result, trajectory, plt_3d, plt_2d
end

# Запуск тестов
println("Метод Хука-Дживса: Тестирование на трёх функциях")

# Тест 1: Розенброк
x0_rosenbrock = [-2.0, -2.0]
result_a1, traj_a1, plt_3d_a1, plt_2d_a1 = test_function(rosenbrock, "Розенброк", x0_rosenbrock, (-2.0, 2.0), (-2.0, 2.0), "a")
result_b1, traj_b1, plt_3d_b1, plt_2d_b1 = test_function(rosenbrock, "Розенброк", x0_rosenbrock, (-2.0, 2.0), (-2.0, 2.0), "b")

# Тест 2: Растригин
x0_rastrigin = [0.5, 0.5]
result_a2, traj_a2, plt_3d_a2, plt_2d_a2 = test_function(rastrigin, "Растригин", x0_rastrigin, (-5.0, 5.0), (-5.0, 5.0), "a")
result_b2, traj_b2, plt_3d_b2, plt_2d_b2 = test_function(rastrigin, "Растригин", x0_rastrigin, (-5.0, 5.0), (-5.0, 5.0), "b")

# Тест 3: Швефель
x0_schwefel = [0.5, 0.5]
result_a3, traj_a3, plt_3d_a3, plt_2d_a3 = test_function(schwefel, "Швефель", x0_schwefel, (-500.0, 500.0), (-500.0, 500.0), "a")
result_b3, traj_b3, plt_3d_b3, plt_2d_b3 = test_function(schwefel, "Швефель", x0_schwefel, (-500.0, 500.0), (-500.0, 500.0), "b")

# Отображение графиков
println("\nОтображение графиков...")
display(plt_3d_a1)
display(plt_2d_a1)
display(plt_3d_b1)
display(plt_2d_b1)
display(plt_3d_a2)
display(plt_2d_a2)
display(plt_3d_b2)
display(plt_2d_b2)
display(plt_3d_a3)
display(plt_2d_a3)
display(plt_3d_b3)
display(plt_2d_b3)

