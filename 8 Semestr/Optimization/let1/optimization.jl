function f(x::Float64)::Float64
    return (x - 3.0)^2 + 5.0
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
        
        k += 1
    end
    
    x_min = (a_k + b_k) / 2.0
    f_min = f(x_min)
    
    println("\nРезультат:")
    println("Точка минимума: x* = $x_min")
    println("Значение функции: f(x*) = $f_min")
    println("Заданная точность: $epsilon")
    println("Достигнутая точность: $(abs(b_k - a_k))")
    
    return x_min, f_min, epsilon
end

function check_unimodality(f::Function, a::Float64, b::Float64, n_points::Int = 1000)
    println("ПРОВЕРКА УНИМОДАЛЬНОСТИ")
    
    h = (b - a) / n_points
    x_points = [a + i * h for i in 0:n_points]
    
    sign_changes = 0
    prev_derivative = numerical_derivative(f, x_points[1])
    
    min_derivative = prev_derivative
    max_derivative = prev_derivative
    
    for i in 2:length(x_points)
        current_derivative = numerical_derivative(f, x_points[i])
        
        if prev_derivative < 0 && current_derivative > 0
            sign_changes += 1
            println("Найдена точка смены знака производной: x ≈ $(x_points[i])")
        end
        
        min_derivative = min(min_derivative, current_derivative)
        max_derivative = max(max_derivative, current_derivative)
        
        prev_derivative = current_derivative
    end
    
    println("Количество смен знака производной (отрицательного на положительный): $sign_changes")
    println("Минимальное значение производной: $min_derivative")
    println("Максимальное значение производной: $max_derivative")
    
    if sign_changes == 1
        return true
    elseif sign_changes == 0
        return false
    else
        return false
    end
end

function main()
    println("ПОИСК МИНИМУМА ФУНКЦИИ f(x) = (x - 3)² + 5")
    
    x0 = 0.0
    delta = 0.1
    
    (a, b) = svenn_method(f, x0, delta)
    println("\nНайденный интервал локализации: [$a, $b]")
    
    is_unimodal = check_unimodality(f, a, b)
    
    if !is_unimodal
        println("Предупреждение: функция может не быть унимодальной на найденном интервале")
    end
    
    epsilon = 1e-5
    x_min, f_min, precision = fibonacci_method(f, a, b, epsilon)
end

main()

