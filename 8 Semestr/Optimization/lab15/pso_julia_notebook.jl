using Plots
using Random
using Statistics

gr()

# ## 1. Тестовые функции

# Функция Растригина: глобальный минимум в (0, 0), f = 0
function rastrigin(x::AbstractVector{<:Real}; A::Float64 = 10.0)
    n = length(x)
    return A * n + sum(xi^2 - A * cos(2π * xi) for xi in x)
end

# Функция Розенброка: глобальный минимум в (1, 1), f = 0
function rosenbrock(x::AbstractVector{<:Real})
    s = 0.0
    for i in 1:length(x)-1
        s += 100 * (x[i+1] - x[i]^2)^2 + (1 - x[i])^2
    end
    return s
end

# Функция Швефеля: глобальный минимум в (420.9687, 420.9687), f = 0
function schwefel(x::AbstractVector{<:Real})
    n = length(x)
    # Каноническая константа Schwefel 2.26 для более точного f(x*) ≈ 0
    return 418.9828872724338 * n - sum(xi * sin(sqrt(abs(xi))) for xi in x)
end

# ## 2. Простая реализация PSO
# 
# Используем формулу с инерцией:
# 
# \[
# v_{i,t+1} = \omega(t) v_{i,t} + \varphi_p r_p (p_{i,t} - x_{i,t}) + \varphi_g r_g (g_t - x_{i,t})
# \]
# 
# и шаг по координатам:
# 
# \[
# x_{i,t+1} = x_{i,t} + v_{i,t+1}.
# \]
# 
# Для простоты:
# 
# - размерность фиксируем `dim = 2`,
# - ограничиваем скорость через `vmax`,
# - позицию частицы после шага обрезаем по допустимой области.

function pso(
    f;
    bounds = (-5.12, 5.12),
    dim::Int = 2,
    n_particles::Int = 30,
    max_iter::Int = 150,
    c1::Float64 = 1.7,
    c2::Float64 = 1.7,
    w_max::Float64 = 0.9,
    w_min::Float64 = 0.4,
    vmax_ratio::Float64 = 0.25,
    seed::Int = 42,
)
    Random.seed!(seed)

    lo, hi = bounds
    span = hi - lo
    vmax = vmax_ratio * span

    # Начальные позиции и скорости
    X = rand(n_particles, dim) .* span .+ lo
    V = rand(n_particles, dim) .* (0.2 * span) .- 0.1 * span

    # Лучшая позиция каждой частицы
    pbest = copy(X)
    pbest_val = [f(vec(X[i, :])) for i in 1:n_particles]

    # Лучшая позиция всего роя
    best_idx = argmin(pbest_val)
    gbest = copy(vec(pbest[best_idx, :]))
    gbest_val = pbest_val[best_idx]

    # История для графиков и GIF
    history_best = Float64[gbest_val]
    history_pos = [copy(X)]
    history_gbest = [copy(gbest)]

    for t in 1:max_iter
        # Линейно уменьшаем инерцию
        w = w_max - (w_max - w_min) * (t - 1) / max(max_iter - 1, 1)

        for i in 1:n_particles
            r1 = rand(dim)
            r2 = rand(dim)

            V[i, :] .=
                w .* V[i, :] .+
                c1 .* r1 .* (pbest[i, :] .- X[i, :]) .+
                c2 .* r2 .* (gbest .- X[i, :])

            # Ограничение скорости
            V[i, :] .= clamp.(V[i, :], -vmax, vmax)

            # Новый шаг
            X[i, :] .+= V[i, :]

            # Возвращаем в допустимую область
            X[i, :] .= clamp.(X[i, :], lo, hi)

            val = f(vec(X[i, :]))

            # Обновление personal best
            if val < pbest_val[i]
                pbest[i, :] .= X[i, :]
                pbest_val[i] = val

                # Обновление global best
                if val < gbest_val
                    gbest .= X[i, :]
                    gbest_val = val
                end
            end
        end

        push!(history_best, gbest_val)
        push!(history_pos, copy(X))
        push!(history_gbest, copy(gbest))
    end

    return (
        best_pos = copy(gbest),
        best_val = gbest_val,
        history_best = history_best,
        history_pos = history_pos,
        history_gbest = history_gbest,
    )
end

# ## 3. Вспомогательные функции для графиков и анимации

function landscape_grid(f, bounds; n::Int = 200)
    lo, hi = bounds
    xs = collect(range(lo, hi, length=n))
    ys = collect(range(lo, hi, length=n))

    # Z[j, i] соответствует точке (xs[i], ys[j])
    Z = [f([x, y]) for y in ys, x in xs]
    return xs, ys, Z
end

function save_convergence_plot(history_best, title_str, outpath)
    p = plot(
        history_best;
        xlabel = "Итерация",
        ylabel = "Лучшее значение f(gbest)",
        title = "Сходимость PSO: " * title_str,
        lw = 2,
        legend = false,
        grid = true,
        size = (800, 500),
    )
    savefig(p, outpath)
    return p
end

function save_swarm_gif(
    f,
    bounds,
    history_pos,
    history_gbest,
    true_min,
    title_str,
    outpath;
    every::Int = 5,
    grid_n::Int = 180,
)
    xs, ys, Z = landscape_grid(f, bounds; n=grid_n)

    idxs = collect(1:every:length(history_pos))
    if idxs[end] != length(history_pos)
        push!(idxs, length(history_pos))
    end

    anim = @animate for k in idxs
        pos = history_pos[k]
        gb = history_gbest[k]

        p = contour(
            xs,
            ys,
            Z;
            fill = true,
            levels = 30,
            c = :viridis,
            xlabel = "x₁",
            ylabel = "x₂",
            title = title_str * ", итерация " * string(k - 1),
            size = (700, 700),
            legend = :topright,
        )

        scatter!(p, pos[:, 1], pos[:, 2];
            color = :red,
            markersize = 3,
            markerstrokecolor = :black,
            label = "частицы",
        )

        scatter!(p, [gb[1]], [gb[2]];
            color = :cyan,
            markershape = :star5,
            markersize = 9,
            markerstrokecolor = :black,
            label = "gbest",
        )

        scatter!(p, [true_min[1]], [true_min[2]];
            color = :white,
            markershape = :xcross,
            markersize = 8,
            markerstrokecolor = :black,
            label = "истинный минимум",
        )

        xlims!(p, bounds)
        ylims!(p, bounds)

        p
    end

    gif(anim, outpath, fps = 8)
end

# ## 4. Запуск на трёх функциях
# 
# Для Швефеля берём чуть больше частиц и итераций, потому что функция сильно мультимодальная.

mkpath("pso_results")

benchmarks = Dict(
    "Rastrigin" => (
        f = rastrigin,
        bounds = (-5.12, 5.12),
        true_min = [0.0, 0.0],
        true_val = 0.0,
        n_particles = 35,
        max_iter = 150,
        c1 = 1.7,
        c2 = 1.7,
        vmax_ratio = 0.25,
        seed = 12,
        every = 5,
    ),
    "Rosenbrock" => (
        f = rosenbrock,
        bounds = (-3.0, 3.0),
        true_min = [1.0, 1.0],
        true_val = 0.0,
        n_particles = 35,
        max_iter = 150,
        c1 = 1.7,
        c2 = 1.7,
        vmax_ratio = 0.20,
        seed = 12,
        every = 5,
    ),
    "Schwefel" => (
        f = schwefel,
        bounds = (-500.0, 500.0),
        true_min = [420.968746, 420.968746],
        true_val = 0.0,
        n_particles = 60,
        max_iter = 300,
        c1 = 1.8,
        c2 = 1.8,
        vmax_ratio = 0.30,
        seed = 42,
        every = 10,
    ),
)

results = Dict()

for (name, cfg) in benchmarks
    result = pso(
        cfg.f;
        bounds = cfg.bounds,
        n_particles = cfg.n_particles,
        max_iter = cfg.max_iter,
        c1 = cfg.c1,
        c2 = cfg.c2,
        vmax_ratio = cfg.vmax_ratio,
        seed = cfg.seed,
    )

    results[name] = result

    println("======================================================")
    println(name)
    println("Найденная точка минимума: ", result.best_pos)
    println("Найденное значение:       ", result.best_val)
    println("Ожидаемая точка:          ", cfg.true_min)
    println("Ожидаемое значение:       ", cfg.true_val)

    conv_path = joinpath("pso_results", lowercase(name) * "_convergence.png")
    gif_path  = joinpath("pso_results", lowercase(name) * "_swarm.gif")

    save_convergence_plot(result.history_best, name, conv_path)
    save_swarm_gif(
        cfg.f,
        cfg.bounds,
        result.history_pos,
        result.history_gbest,
        cfg.true_min,
        name,
        gif_path;
        every = cfg.every,
    )
end

# ## 5. Сводная таблица результатов

println()
println("ИТОГИ:")
println("--------------------------------------------------------------")
println(rpad("Функция", 15), rpad("x*", 30), "f(x*)")
println("--------------------------------------------------------------")

for name in ["Rastrigin", "Rosenbrock", "Schwefel"]
    r = results[name]
    println(rpad(name, 15), rpad(string(round.(r.best_pos; digits=6)), 30), round(r.best_val; digits=8))
end

# ## 6. Дополнительные графики, как в конспекте
# 
# ### 6.1. Влияние числа частиц на сходимость

function compare_particle_counts(f, bounds, counts, outpath; max_iter=120)
    p = plot(
        xlabel = "Итерация",
        ylabel = "Лучшее значение",
        title = "Влияние числа частиц",
        grid = true,
        size = (800, 500),
    )

    for (j, n) in enumerate(counts)
        result = pso(
            f;
            bounds = bounds,
            n_particles = n,
            max_iter = max_iter,
            c1 = 1.7,
            c2 = 1.7,
            vmax_ratio = 0.25,
            seed = 100 + j,
        )
        plot!(p, result.history_best; lw=2, label="N = $n")
    end

    savefig(p, outpath)
    return p
end

compare_particle_counts(
    rastrigin,
    (-5.12, 5.12),
    [10, 25, 50],
    joinpath("pso_results", "compare_particles.png");
    max_iter = 120,
)

# ### 6.2. Влияние параметра `φg` на сходимость

function compare_phi_g(f, bounds, phi_values, outpath; max_iter=120)
    p = plot(
        xlabel = "Итерация",
        ylabel = "Лучшее значение",
        title = "Влияние параметра φg",
        grid = true,
        size = (800, 500),
    )

    for (j, phi_g) in enumerate(phi_values)
        result = pso(
            f;
            bounds = bounds,
            n_particles = 30,
            max_iter = max_iter,
            c1 = 1.7,
            c2 = phi_g,
            vmax_ratio = 0.25,
            seed = 200 + j,
        )
        plot!(p, result.history_best; lw=2, label="φg = $phi_g")
    end

    savefig(p, outpath)
    return p
end

compare_phi_g(
    rastrigin,
    (-5.12, 5.12),
    [0.8, 1.7, 3.0],
    joinpath("pso_results", "compare_phi_g.png");
    max_iter = 120,
)

# ## 7. Что должно получиться после запуска
# 
# В папке `pso_results/` появятся файлы:
# 
# - `rastrigin_convergence.png`
# - `rastrigin_swarm.gif`
# - `rosenbrock_convergence.png`
# - `rosenbrock_swarm.gif`
# - `schwefel_convergence.png`
# - `schwefel_swarm.gif`
# - `compare_particles.png`
# - `compare_phi_g.png`
# 
# Этого уже достаточно для отчёта или демонстрации на защите.