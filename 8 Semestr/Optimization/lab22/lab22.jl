
using Random, Plots

function f(x)
    s = 0.0
    for i in 1:11
        a_i = 2.0 * i
        b_i = (2.0 * i)^4
        s += a_i - x[1] * (b_i^2 + b_i * x[2]) / (b_i^2 + b_i * x[3] + x[4])
    end
    return s
end

function ais_optimize(Np=50, s=10, d=10, K=30, η=0.6, α=-1.0, β=10.0)
    Random.seed!(42)
    pop = [[α + (β - α) * rand() for _ in 1:4] for _ in 1:Np]
    fit = [f(ind) for ind in pop]
    history = Float64[]

    for _ in 1:K
        order = sortperm(fit)

        for j in 1:s # клонируем s лучших клеток
            parent_idx = order[j]
            parent = pop[parent_idx]
            parent_fit = fit[parent_idx] # 2.1 упорядочили по возрастанию f

            Nc = max(1, floor(Int, η * Np / j)) # 2. 2 чем лучше родитель, тем больше клонов
            clones = [copy(parent) for _ in 1:Nc] # На этом этапе родители + клоны NP + sum

            for clone in clones
                for i in 1:4
                    while true 
                        u = rand() #3 мутируем u - нормальный закон распределения
                        if u > 0.5
                            new_val = clone[i] + rand() * (β - clone[i])
                        else
                            new_val = clone[i] - rand() * (clone[i] - α)
                        end
                        if α <= new_val <= β
                            clone[i] = new_val
                            break
                        end
                    end
                end
            end # На этом этапе модифицированные клоны + родители NP + sum

            clones_fit = [f(c) for c in clones] 
            best_idx = argmin(clones_fit)
            best_clone = clones[best_idx]
            best_fit = clones_fit[best_idx]

            if best_fit < parent_fit # 4.2 Выбираем лучшего среди родителя и его порождений -> NP + sum
                pop[parent_idx] = best_clone
                fit[parent_idx] = best_fit
            end
        end

        order = sortperm(fit) # перегенерируем d худших клеток -> NP
        worst = order[end-d+1:end]
        for idx in worst
            new_ind = [α + (β - α) * rand() for _ in 1:4]
            pop[idx] = new_ind
            fit[idx] = f(new_ind)
        end

        push!(history, abs(minimum(fit)))
    end

    best_idx = argmin(fit)
    return pop[best_idx], fit[best_idx], history
end

best_x, best_f, history = ais_optimize()
println(best_x)
println(best_f)

plot(1:length(history), history, xlabel="Итерация", ylabel="|f_min|", title="Сходимость AIS", legend=false, lw=2)
savefig("lab22/convergence.png")

# клоны, мутации клонов, отбор, зачистка 