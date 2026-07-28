const LAB22_ROOT = pwd()
using Random, Statistics, LinearAlgebra
using Plots

default(; size = (800, 420), fmt = :png, show = true)

plot_cache_dir() = mkpath(joinpath(LAB22_ROOT, ".plot_display_cache"))

gif_frames_root() = mkpath(joinpath(plot_cache_dir(), "gif_frames"))

gif_frames_dir(prefix::AbstractString = "lab22_") = mkpath(joinpath(gif_frames_root(), prefix * string(time_ns())))

function showplot(p = Plots.current())
    d = plot_cache_dir()
    path = joinpath(d, string(time_ns(), ".png"))
    try
        Plots.savefig(p, path)
        try
            display(MIME("image/png"), read(path))
        catch
            # Fallback for non-notebook runs
            display(p)
        end
    finally
        rm(path; force = true)
    end
    Plots.closeall()
    return nothing
end

function showgif(path::AbstractString)
    try
        display(MIME("image/gif"), read(path))
    catch
        println("GIF saved at: ", path)
    end
    return nothing
end


# Test functions for minimization

sphere(x) = sum(abs2, x)

function rosenbrock(x)
    s = 0.0
    for i in 1:(length(x) - 1)
        s += 100.0 * (x[i+1] - x[i]^2)^2 + (1.0 - x[i])^2
    end
    return s
end

rastrigin(x) = 10.0 * length(x) + sum(xi^2 - 10.0 * cos(2pi*xi) for xi in x)

function ackley(x)
    n = length(x)
    a, b, c = 20.0, 0.2, 2pi
    s1 = sum(abs2, x)
    s2 = sum(cos(c*xi) for xi in x)
    return -a * exp(-b * sqrt(s1 / n)) - exp(s2 / n) + a + exp(1)
end

function griewank(x)
    s = sum(abs2, x) / 4000.0
    p = prod(cos(x[i] / sqrt(i)) for i in eachindex(x))
    return s - p + 1.0
end

# Variant 2 (from assignment):
# f₂(x) = ( 1/200 + Σ_{j=1..10} 1/( j + Σ_{i=1..2} (x_i - a_{ij})^4 ) )^{-1}
# n = 2, a_{ij} = i + j, x_i ∈ [0, 5]
function variant2(x)
    @assert length(x) == 2
    s = 0.0
    for j in 1:10
        inner = 0.0
        for i in 1:2
            aij = i + j
            inner += (x[i] - aij)^4
        end
        s += 1.0 / (j + inner)
    end
    return 1.0 / (1.0 / 200.0 + s)
end

TEST_FUNCS = Dict(
    "variant2" => (variant2, (0.0, 5.0)),
    "sphere" => (sphere, (-5.12, 5.12)),
    "rosenbrock" => (rosenbrock, (-5.0, 10.0)),
    "rastrigin" => (rastrigin, (-5.12, 5.12)),
    "ackley" => (ackley, (-32.768, 32.768)),
    "griewank" => (griewank, (-600.0, 600.0))
);


struct AISResult
    best_x::Vector{Float64}
    best_f::Float64
    best_trace::Vector{Float64}
end

clamp_vec(x, lo, hi) = map(xi -> clamp(xi, lo, hi), x)

function init_population(Np::Int, dim::Int, lo::Float64, hi::Float64; rng=Random.default_rng())
    return [lo .+ (hi - lo) .* rand(rng, dim) for _ in 1:Np]
end

function evaluate_population(f, pop)
    vals = [f(x) for x in pop]
    return vals
end

function select_best(pop, vals, s::Int)
    idx = sortperm(vals)
    idxs = idx[1:s]
    return pop[idxs], vals[idxs], idx
end

# Clonal selection with rank-based cloning and affinity-dependent mutation.
# Lower objective value => higher affinity.
function immune_optimize(
    f;
    dim::Int,
    bounds::Tuple{Float64,Float64},
    Np::Int = 60,
    s::Int = 10,
    d::Int = 10,
    K::Int = 200,
    Nc::Int = 80,
    rho::Float64 = 2.5,
    sigma0::Float64 = 0.2,
    seed::Int = 42
)
    res, _ = immune_optimize_history(
        f;
        dim,
        bounds,
        Np,
        s,
        d,
        K,
        Nc,
        rho,
        sigma0,
        seed,
        record_every = 0,
    )
    return res
end

"""
Variant of AIS that can record population snapshots for visualization.

- record_every = 0: don't record anything (fast)
- record_every = k>0: store population every k iterations + first iteration

Returns: (AISResult, history::Vector{Vector{Vector{Float64}}})
"""
function immune_optimize_history(
    f;
    dim::Int,
    bounds::Tuple{Float64,Float64},
    Np::Int = 60,
    s::Int = 10,
    d::Int = 10,
    K::Int = 200,
    Nc::Int = 80,
    rho::Float64 = 2.5,
    sigma0::Float64 = 0.2,
    seed::Int = 42,
    record_every::Int = 1,
)
    lo, hi = bounds
    rng = MersenneTwister(seed)

    pop = init_population(Np, dim, lo, hi; rng)
    vals = evaluate_population(f, pop)

    best_i = argmin(vals)
    best_x = copy(pop[best_i])
    best_f = vals[best_i]
    trace = Float64[best_f]

    history = Vector{Vector{Vector{Float64}}}()
    if record_every > 0
        push!(history, [copy(x) for x in pop])
    end

    weights = collect(s:-1:1)
    wsum = sum(weights)

    for it in 1:K
        elites, elite_vals, _ = select_best(pop, vals, s)
        fmin, fmax = minimum(elite_vals), maximum(elite_vals)
        denom = max(fmax - fmin, eps())

        clones = Vector{Vector{Float64}}()
        clone_vals = Float64[]

        for (rank, x) in enumerate(elites)
            ncl = max(1, round(Int, Nc * weights[rank] / wsum))
            affinity = 1.0 - (elite_vals[rank] - fmin) / denom
            σ = sigma0 * (hi - lo) * exp(-rho * affinity)
            for _ in 1:ncl
                y = x .+ σ .* randn(rng, dim)
                y = clamp_vec(y, lo, hi)
                push!(clones, y)
                push!(clone_vals, f(y))
            end
        end

        merged = vcat(pop, clones)
        merged_vals = vcat(vals, clone_vals)
        merged_order = sortperm(merged_vals)
        pop = merged[merged_order[1:Np]]
        vals = merged_vals[merged_order[1:Np]]

        d_eff = min(d, Np)
        for j in 0:(d_eff-1)
            xnew = lo .+ (hi - lo) .* rand(rng, dim)
            pop[end - j] = xnew
            vals[end - j] = f(xnew)
        end

        bi = argmin(vals)
        if vals[bi] < best_f
            best_f = vals[bi]
            best_x = copy(pop[bi])
        end
        push!(trace, best_f)

        if record_every > 0 && (it % record_every == 0)
            push!(history, [copy(x) for x in pop])
        end
    end

    return AISResult(best_x, best_f, trace), history
end

function ais_make_gif_2d(
    f;
    bounds::Tuple{Float64,Float64},
    out_path::AbstractString = joinpath(LAB22_ROOT, "ais_evolution.gif"),
    frames_dir::AbstractString = gif_frames_dir("ais_gif_"),
    Np::Int = 60,
    s::Int = 10,
    d::Int = 10,
    K::Int = 200,
    Nc::Int = 80,
    rho::Float64 = 2.5,
    sigma0::Float64 = 0.2,
    seed::Int = 1,
    record_every::Int = 2,
    fps::Real = 12,
    grid_n::Int = 120,
)
    lo, hi = bounds

    res, hist = immune_optimize_history(
        f;
        dim = 2,
        bounds,
        Np,
        s,
        d,
        K,
        Nc,
        rho,
        sigma0,
        seed,
        record_every,
    )

    xs = range(lo, hi; length = grid_n)
    ys = range(lo, hi; length = grid_n)
    Z = [f([x, y]) for y in ys, x in xs]

    anim = Animation(frames_dir, String[])
    prev_show = Plots.default(:show)
    default(show = false)
    try
        nframes = length(hist)
        for i in 1:nframes
            pop = hist[i]
            px = first.(pop)
            py = last.(pop)

            p = contour(
                xs,
                ys,
                log10.(Z .+ 1e-12);
                title = "AIS, frame $i / $nframes",
                xlabel = "x1",
                ylabel = "x2",
                colorbar = false,
                levels = 20,
                legend = :topright,
            )
            scatter!(p, px, py; ms = 3, alpha = 0.65, label = "pop")
            scatter!(p, [res.best_x[1]], [res.best_x[2]]; ms = 6, marker = :star5, label = "best")

            frame(anim)
            closeall()
        end
        gif(anim, String(out_path); fps = fps)
    finally
        default(show = prev_show)
        closeall()
    end

    return out_path, frames_dir, res
end


name = "variant2"  # вариант 2 из методички
f, bounds = TEST_FUNCS[name]

dim = 2
res = immune_optimize(f; dim, bounds, Np=80, s=12, d=12, K=250, Nc=120, rho=2.5, sigma0=0.25, seed=1)

println("Function: ", name)
println("Best f: ", res.best_f)
println("Best x: ", res.best_x)

p = plot(res.best_trace; xlabel="iteration", ylabel="best f", title="AIS convergence: $name (dim=$dim)", yscale=:log10, legend=false)
showplot(p)


# GIF работы алгоритма (2D визуализация)

gif_name = "variant2"
fg, bg = TEST_FUNCS[gif_name]

out_gif = joinpath(LAB22_ROOT, "lab22_ais_$(gif_name).gif")
path, frames_dir, res2 = ais_make_gif_2d(
    fg;
    bounds = bg,
    out_path = out_gif,
    Np = 70,
    s = 12,
    d = 10,
    K = 180,
    Nc = 120,
    rho = 2.5,
    sigma0 = 0.25,
    seed = 2,
    record_every = 2,
    fps = 12,
)

@info "GIF saved" path frames_dir
println("best f (2D): ", res2.best_f)
showgif(path)
