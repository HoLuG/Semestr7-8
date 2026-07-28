using Plots

function f(x::Float64)::Float64
    return cosh(x)
end

function numerical_derivative(f::Function, x::Float64, h::Float64 = 1e-6)::Float64
    return (f(x + h) - f(x - h)) / (2.0 * h)
end

function numerical_second_derivative(f::Function, x::Float64, h::Float64 = 1e-6)::Float64
    return (f(x + h) - 2.0 * f(x) + f(x - h)) / (h^2)
end

function svenn_method(f::Function, x0::Float64, delta::Float64 = 0.01)
    println("МЕТОД СВЕННА")
    f0 = f(x0)
    f_plus = f(x0 + delta)
    f_minus = f(x0 - delta)
    
    println("x0 = $x0, f(x0) = $f0")
    println("f(x0 + δ) = $f_plus, f(x0 - δ) = $f_minus")
    
    if f_minus < f0 && f0 < f_plus
        direction = -1.0
    elseif f_plus < f0 && f0 < f_minus
        direction = 1.0
    elseif f_minus > f0 && f_plus > f0
        return (x0 - delta, x0 + delta)
    else
        direction = 1.0
    end
    

    a = x0
    b = x0
    step = delta
    k = 0
    
    while true
        k += 1
        x_new = b + direction * step
        f_new = f(x_new)
        f_b = f(b)
        
        if f_new > f_b
            if direction > 0
                return (a, x_new)
            else
                return (x_new, a)
            end
        else
            a = b
            b = x_new
            step *= 2.0
        end
        
        if k > 100
            break
        end
    end
    
    if direction > 0
        return (a, b)
    else
        return (b, a)
    end
end

function fibonacci_method(f::Function, a::Float64, b::Float64, epsilon::Float64)
    println("МЕТОД ФИБОНАЧЧИ")

    n = 1
    fib_n = 1.0
    fib_n1 = 1.0
    
    while (b - a) / fib_n1 > epsilon
        n += 1
        temp = fib_n1
        fib_n1 = fib_n + fib_n1
        fib_n = temp
    end
    
    println("Начальный интервал: [$a, $b]")
    println("Требуемая точность: $epsilon")
    println("Количество итераций: $n")
    
    fib = Vector{Float64}(undef, n + 1)
    fib[1] = 1.0
    fib[2] = 1.0
    for i in 3:(n+1)
        fib[i] = fib[i-1] + fib[i-2]
    end
    
    a_k = a
    b_k = b
    k = 1
    
    iteration_history = Vector{Tuple{Float64, Float64}}()
    push!(iteration_history, ((a_k + b_k) / 2.0, f((a_k + b_k) / 2.0)))
    
    while k < n
        idx = n - k
        if idx >= 1
            lambda_k = a_k + (fib[idx] / fib[idx+2]) * (b_k - a_k)
            mu_k = a_k + (fib[idx+1] / fib[idx+2]) * (b_k - a_k)
        else
            lambda_k = a_k + (fib[1] / fib[3]) * (b_k - a_k)
            mu_k = lambda_k + epsilon
            if mu_k > b_k
                mu_k = b_k
            end
        end
        
        f_lambda = f(lambda_k)
        f_mu = f(mu_k)
        
        if f_lambda > f_mu
            a_k = lambda_k
        else
            b_k = mu_k
        end
        
        push!(iteration_history, ((a_k + b_k) / 2.0, f((a_k + b_k) / 2.0)))
        k += 1
    end
    
    x_min = (a_k + b_k) / 2.0
    f_min = f(x_min)
    
    println("\nРезультат:")
    println("Точка минимума: x* = $x_min")
    println("Значение функции: f(x*) = $f_min")
    println("Заданная точность: $epsilon")
    println("Достигнутая точность: $(abs(b_k - a_k))")
    println("Количество итераций: $(length(iteration_history))")
    
    return x_min, f_min, epsilon, iteration_history
end

function backward_variable_step_method(f::Function, a::Float64, b::Float64, epsilon::Float64)
    println("МЕТОД ОБРАТНОГО ПЕРЕМЕННОГО ШАГА")
    
    iteration_history = Vector{Tuple{Float64, Float64}}()
    
    a_k = a
    b_k = b
    k = 0
    
    while (b_k - a_k) > epsilon
        k += 1
        x1 = (a_k + b_k) / 2.0 - epsilon / 4.0
        x2 = (a_k + b_k) / 2.0 + epsilon / 4.0
        
        f1 = f(x1)
        f2 = f(x2)
        
        push!(iteration_history, (x1, f1))
        push!(iteration_history, (x2, f2))
        
        if f1 < f2
            b_k = x2
        else
            a_k = x1
        end
    end
    
    x_min = (a_k + b_k) / 2.0
    f_min = f(x_min)
    push!(iteration_history, (x_min, f_min))
    
    println("\nРезультат:")
    println("Точка минимума: x* = $x_min")
    println("Значение функции: f(x*) = $f_min")
    println("Заданная точность: $epsilon")
    println("Достигнутая точность: $(abs(b_k - a_k))")
    println("Количество итераций: $k")
    
    return x_min, f_min, epsilon, iteration_history
end

function quad_vertex(x0::Float64, y0::Float64, x1::Float64, y1::Float64, x2::Float64, y2::Float64)
    num = (x1 - x0)^2 * (y1 - y2) - (x1 - x2)^2 * (y1 - y0)
    den = (x1 - x0) * (y1 - y2) - (x1 - x2) * (y1 - y0)
    if abs(den) < 1e-10
        return (x0 + x1 + x2) / 3.0
    end
    return x1 - 0.5 * (num / den)
end

function quad_interp(x::Float64, x0::Float64, y0::Float64, x1::Float64, y1::Float64, x2::Float64, y2::Float64)
    return y0 * (x - x1) * (x - x2) / ((x0 - x1) * (x0 - x2)) +
           y1 * (x - x0) * (x - x2) / ((x1 - x0) * (x1 - x2)) +
           y2 * (x - x0) * (x - x1) / ((x2 - x0) * (x2 - x1))
end

function powell_method(f::Function, a::Float64, b::Float64, epsilon::Float64)
    println("МЕТОД ПАУЭЛА")
    
    iteration_history = Vector{Tuple{Float64, Float64}}()
    parabola_history = Vector{Tuple{Float64, Float64, Float64, Float64, Float64, Float64}}()
    
    x1 = a
    x2 = (a + b) / 2.0
    x3 = b
    
    f1 = f(x1)
    f2 = f(x2)
    f3 = f(x3)
    
    push!(iteration_history, (x1, f1))
    push!(iteration_history, (x2, f2))
    push!(iteration_history, (x3, f3))
    
    a_k = a
    b_k = b
    k = 0
    
    while (b_k - a_k) > epsilon && k < 10000
        k += 1
        
        push!(parabola_history, (Float64(x1), Float64(f1), Float64(x2), Float64(f2), Float64(x3), Float64(f3)))
        
        denom = f1*(x2-x3) + f2*(x3-x1) + f3*(x1-x2)
        use_fallback = false
        x_new = nothing
        
        if abs(denom) > 1e-15 && abs(x3 - x1) > epsilon
            x_new = 0.5 * (f1*(x2^2-x3^2) + f2*(x3^2-x1^2) + f3*(x1^2-x2^2)) / denom
            x_new = max(a_k + epsilon, min(b_k - epsilon, x_new))
            
            if abs(x_new - x1) < epsilon || abs(x_new - x2) < epsilon || abs(x_new - x3) < epsilon
                use_fallback = true
            end
        else
            use_fallback = true
        end
        
        if use_fallback
            golden_ratio = 0.3819660112501051
            if f1 < f3
                x_new = a_k + golden_ratio * (b_k - a_k)
            else
                x_new = b_k - golden_ratio * (b_k - a_k)
            end
            x_new = max(a_k + epsilon, min(b_k - epsilon, x_new))
        end
        
        f_new = f(x_new)
        push!(iteration_history, (x_new, f_new))
        
        if x_new < x2
            if f_new < f2
                x3 = x2
                f3 = f2
                x2 = x_new
                f2 = f_new
            else
                x1 = x_new
                f1 = f_new
            end
        else
            if f_new < f2
                x1 = x2
                f1 = f2
                x2 = x_new
                f2 = f_new
            else
                x3 = x_new
                f3 = f_new
            end
        end
        
        a_k = x1
        b_k = x3
    end
    
    x_min_final = x2
    f_min_final = f2
    
    println("\nРезультат:")
    println("Точка минимума: x* = $x_min_final")
    println("Значение функции: f(x*) = $f_min_final")
    println("Заданная точность: $epsilon")
    println("Количество итераций: $k")
    println("Количество сохраненных парабол: $(length(parabola_history))")
    
    return x_min_final, f_min_final, epsilon, iteration_history, parabola_history, k
end

function check_unimodality(f::Function, a::Float64, b::Float64, n_points::Int = 1000)
    println("\nПРОВЕРКА УНИМОДАЛЬНОСТИ")
    
    x_points = range(a, b, length=n_points)
    signs = [sign(numerical_derivative(f, x)) for x in x_points]
    
    changes = 0
    cur = signs[1]
    
    for s in signs[2:end]
        if s != cur
            changes += 1
            cur = s
        end
    end
    
    is_unimodal = (changes <= 1)
    
    if is_unimodal
        println("Функция унимодальна на интервале [$a, $b]")
    else
        println("Функция может не быть унимодальной на интервале [$a, $b]")
    end
    
    return is_unimodal
end

function check_rain_rule(f::Function, x_min::Float64, epsilon::Float64, delta::Float64 = 1e-4)
    println("\nПРОВЕРКА МИНИМУМА ПО ПРАВИЛУ ДОЖДЯ")
    
    f_min = f(x_min)
    test_points = [
        x_min - delta,
        x_min - epsilon,
        x_min,
        x_min + epsilon,
        x_min + delta
    ]
    
    all_greater = true
    println("Проверка точки минимума x* = $x_min, f(x*) = $f_min")
    println("Проверяем окрестность точки минимума:")
    
    for x_test in test_points
        if abs(x_test - x_min) > 1e-10
            f_test = f(x_test)
            println("  f($x_test) = $f_test")
            if f_test < f_min - 1e-10
                all_greater = false
            end
        end
    end
    
    if all_greater
        println("Правило дождя выполнено")
    else
        println("Правило дождя не выполнено")
    end
    
    return all_greater
end

function visualize_results(f::Function, a::Float64, b::Float64, epsilon::Float64,
                           fib_result::Tuple, backward_result::Tuple, powell_result::Tuple)
    x_min_fib, f_min_fib, _, hist_fib = fib_result
    x_min_back, f_min_back, _, hist_back = backward_result
    if length(powell_result) == 6
        x_min_pow, f_min_pow, _, hist_pow, parabola_history, _ = powell_result
    elseif length(powell_result) == 5
        x_min_pow, f_min_pow, _, hist_pow, parabola_history = powell_result
    else
        x_min_pow, f_min_pow, _, hist_pow = powell_result
        parabola_history = Vector{Tuple{Float64, Float64, Float64, Float64, Float64, Float64}}()
    end
    
    interval_width = max(b - a, 1.0)
    x_range = range(a - 0.3 * interval_width, b + 0.3 * interval_width, length=1000)
    y_range = [f(x) for x in x_range]
    y_range_values = [f(x) for x in x_range]
    y_span = maximum(y_range_values) - minimum(y_range_values)
    vertical_line_height = max(0.1 * y_span, 0.1)
    
    x_fib = [point[1] for point in hist_fib]
    y_fib = [point[2] for point in hist_fib]
    
    x_back = [point[1] for point in hist_back]
    y_back = [point[2] for point in hist_back]
    
    x_pow = [point[1] for point in hist_pow]
    y_pow = [point[2] for point in hist_pow]
    
    p1 = plot(x_range, y_range, 
              linewidth=2, 
              label="f(x) = cosh(x)",
              title="Метод Фибоначчи",
              xlabel="x",
              ylabel="f(x)",
              legend=:topright)
    
    scatter!(p1, x_fib, y_fib, 
             markershape=:x, 
             markersize=8,
             markercolor=:red,
             label="Итерации")
    
    x_min_plot = x_min_fib
    y_min_plot = f_min_fib
    plot!(p1, [x_min_plot - epsilon, x_min_plot + epsilon], 
          [y_min_plot, y_min_plot],
          linewidth=3,
          linecolor=:green,
          linestyle=:dash,
          label="Интервал точности (ε=$epsilon)")
    plot!(p1, [x_min_plot - epsilon, x_min_plot - epsilon],
          [y_min_plot - vertical_line_height, y_min_plot + vertical_line_height],
          linewidth=2,
          linecolor=:green,
          linestyle=:dash,
          label="")
    plot!(p1, [x_min_plot + epsilon, x_min_plot + epsilon],
          [y_min_plot - vertical_line_height, y_min_plot + vertical_line_height],
          linewidth=2,
          linecolor=:green,
          linestyle=:dash,
          label="")
    
    p2 = plot(x_range, y_range,
              linewidth=2,
              label="f(x) = cosh(x)",
              title="Метод обратного переменного шага",
              xlabel="x",
              ylabel="f(x)",
              legend=:topright)
    
    scatter!(p2, x_back, y_back,
             markershape=:x,
             markersize=8,
             markercolor=:blue,
             label="Итерации")
    
    x_min_plot2 = x_min_back
    y_min_plot2 = f_min_back
    plot!(p2, [x_min_plot2 - epsilon, x_min_plot2 + epsilon],
          [y_min_plot2, y_min_plot2],
          linewidth=3,
          linecolor=:green,
          linestyle=:dash,
          label="Интервал точности (ε=$epsilon)")
    plot!(p2, [x_min_plot2 - epsilon, x_min_plot2 - epsilon],
          [y_min_plot2 - vertical_line_height, y_min_plot2 + vertical_line_height],
          linewidth=2,
          linecolor=:green,
          linestyle=:dash,
          label="")
    plot!(p2, [x_min_plot2 + epsilon, x_min_plot2 + epsilon],
          [y_min_plot2 - vertical_line_height, y_min_plot2 + vertical_line_height],
          linewidth=2,
          linecolor=:green,
          linestyle=:dash,
          label="")
    
    if length(x_pow) > 0
        x_pow_min = minimum(x_pow)
        x_pow_max = maximum(x_pow)
        
        if length(parabola_history) > 0
            for quad in parabola_history
                if length(quad) == 6
                    x0q, _, x1q, _, x2q, _ = quad
                    x_pow_min = min(x_pow_min, x0q, x1q, x2q)
                    x_pow_max = max(x_pow_max, x0q, x1q, x2q)
                end
            end
        end
        
        x_pow_span = x_pow_max - x_pow_min
        if x_pow_span < 1e-10
            x_pow_span = max(b - a, 0.1)
        end
        
        x_pow_range_zoom = range(x_pow_min - 0.2 * x_pow_span, x_pow_max + 0.2 * x_pow_span, length=2000)
        y_pow_range_zoom = [f(x) for x in x_pow_range_zoom]
        
        xlims_pow = (x_pow_min - 0.2 * x_pow_span, x_pow_max + 0.2 * x_pow_span)
        y_min_pow = minimum(y_pow_range_zoom)
        y_max_pow = maximum(y_pow_range_zoom)
        y_span_pow = y_max_pow - y_min_pow
        ylims_pow = (y_min_pow - 0.1 * y_span_pow, y_max_pow + 0.1 * y_span_pow)
    else
        x_pow_range_zoom = x_range
        y_pow_range_zoom = y_range
        xlims_pow = nothing
        ylims_pow = nothing
    end
    
    p3 = plot(x_pow_range_zoom, y_pow_range_zoom,
              linewidth=2,
              label="f(x) = cosh(x)",
              title="Метод Пауэла (увеличенный масштаб)",
              xlabel="x",
              ylabel="f(x)",
              legend=:topright,
              xlims=xlims_pow,
              ylims=ylims_pow)
    
    scatter!(p3, x_pow, y_pow,
             markershape=:x,
             markersize=8,
             markercolor=:purple,
             label="Итерации")
    
    x_min_plot3 = x_min_pow
    y_min_plot3 = f_min_pow
    plot!(p3, [x_min_plot3 - epsilon, x_min_plot3 + epsilon],
          [y_min_plot3, y_min_plot3],
          linewidth=3,
          linecolor=:green,
          linestyle=:dash,
          label="Интервал точности (ε=$epsilon)")
    plot!(p3, [x_min_plot3 - epsilon, x_min_plot3 - epsilon],
          [y_min_plot3 - vertical_line_height, y_min_plot3 + vertical_line_height],
          linewidth=2,
          linecolor=:green,
          linestyle=:dash,
          label="")
    plot!(p3, [x_min_plot3 + epsilon, x_min_plot3 + epsilon],
          [y_min_plot3 - vertical_line_height, y_min_plot3 + vertical_line_height],
          linewidth=2,
          linecolor=:green,
          linestyle=:dash,
          label="")
    
    if length(parabola_history) > 0
        parabola_colors = [:orange, :cyan, :magenta, :yellow, :brown, :pink, :lightblue, 
                           :lightgreen, :coral, :lavender, :salmon, :turquoise, :gold, 
                           :plum, :khaki, :tan, :wheat, :thistle, :mistyrose, :lightcyan]
        
        line_styles = [:solid, :dash, :dot, :dashdot, :dashdotdot]
        
        parabolas_drawn = 0
        for (idx, quad) in enumerate(parabola_history)
            if length(quad) == 6
                x0q, y0q, x1q, y1q, x2q, y2q = quad
                x_par_min = min(x0q, x1q, x2q)
                x_par_max = max(x0q, x1q, x2q)
                x_span = x_par_max - x_par_min
                if x_span < 1e-10
                    x_span = 0.1
                end
                
                x_par_range = range(x_par_min - 0.15 * x_span, x_par_max + 0.15 * x_span, length=500)
                y_par_range = [quad_interp(x, x0q, y0q, x1q, y1q, x2q, y2q) for x in x_par_range]
            else
                a_par, b_par, c_par, x_par_min, x_par_max = quad
                x_span = x_par_max - x_par_min
                if x_span < 1e-10
                    x_span = 0.1
                end
                x_par_range = range(x_par_min - 0.1 * x_span, x_par_max + 0.1 * x_span, length=200)
                y_par_range = [a_par * x^2 + b_par * x + c_par for x in x_par_range]
            end
            
            color_idx = ((idx - 1) % length(parabola_colors)) + 1
            style_idx = ((idx - 1) % length(line_styles)) + 1
            
            alpha_val = max(0.4, 1.0 - (idx - 1) * 0.05)
            
            plot!(p3, x_par_range, y_par_range,
                  linewidth=2.0,
                  linecolor=parabola_colors[color_idx],
                  linestyle=line_styles[style_idx],
                  alpha=min(0.8, alpha_val + 0.2),
                  label=(idx == 1 ? "Параболы Пауэла" : ""))
            parabolas_drawn += 1
        end
    end
    
    combined = plot(p1, p2, p3, layout=(3, 1), size=(800, 1200))
    return combined, p1, p2, p3
end

function main()
    println("ПОИСК МИНИМУМА ФУНКЦИИ f(x) = cosh(x) = (e^x + e^(-x))/2")
    println("=" ^ 70)

    x0 = 0.0
    delta = 0.1
    
    (a, b) = svenn_method(f, x0, delta)
    println("\nНайденный интервал локализации: [$a, $b]")
    
    is_unimodal = check_unimodality(f, a, b)
    
    if !is_unimodal
        println("Предупреждение: функция может не быть унимодальной на найденном интервале")
    end
    
    epsilon = 1e-5
    
    println("\n")
    x_min_fib, f_min_fib, _, hist_fib = fibonacci_method(f, a, b, epsilon)
    
    println("\n")
    x_min_back, f_min_back, _, hist_back = backward_variable_step_method(f, a, b, epsilon)
    
    # Метод Пауэла
    println("\n")
    powell_result = powell_method(f, a, b, epsilon)
    if length(powell_result) == 6
        x_min_pow, f_min_pow, _, hist_pow, parabola_history, iter_pow = powell_result
    elseif length(powell_result) == 5
        x_min_pow, f_min_pow, _, hist_pow, parabola_history = powell_result
        iter_pow = length(hist_pow) - 3
    else
        x_min_pow, f_min_pow, _, hist_pow = powell_result
        parabola_history = Vector{Tuple{Float64, Float64, Float64, Float64, Float64, Float64}}()
        iter_pow = length(hist_pow) - 3
    end
    
    println("\n" * "=" ^ 70)
    println("СРАВНЕНИЕ РЕЗУЛЬТАТОВ")
    println("=" ^ 70)
    println("Метод Фибоначчи:")
    println("  x* = $x_min_fib, f(x*) = $f_min_fib, итераций: $(length(hist_fib))")
    println("Метод обратного переменного шага:")
    println("  x* = $x_min_back, f(x*) = $f_min_back, итераций: $(length(hist_back))")
    println("Метод Пауэла:")
    println("  x* = $x_min_pow, f(x*) = $f_min_pow, итераций: $iter_pow")
    
    # Проверка по правилу дождя для всех методов
    println("\n")
    check_rain_rule(f, x_min_fib, epsilon)
    check_rain_rule(f, x_min_back, epsilon)
    check_rain_rule(f, x_min_pow, epsilon)
    
    # Выводы
    println("\n" * "=" ^ 70)
    println("ВЫВОДЫ")
    println("=" ^ 70)
    println("1. Метод Фибоначчи: $(length(hist_fib)) итераций")
    println("2. Метод обратного переменного шага: $(length(hist_back)) итераций")
    println("3. Метод Пауэла: $iter_pow итераций")
    
    min_iter = min(length(hist_fib), length(hist_back), length(hist_pow))
    max_iter = max(length(hist_fib), length(hist_back), length(hist_pow))
    
    
    combined, p1, p2, p3 = visualize_results(f, a, b, epsilon,
                                    (x_min_fib, f_min_fib, epsilon, hist_fib),
                                    (x_min_back, f_min_back, epsilon, hist_back),
                                    powell_result)
    
    savefig(p1, "fibonacci.png")
    savefig(p2, "backward_step.png")
    savefig(p3, "powell.png")
    savefig(combined, "all_methods.png")
end

main()
