using JSON

nb_path = joinpath(@__DIR__, "lab_sa_berlin52.ipynb")
nb = JSON.parsefile(nb_path)

for c in nb["cells"]
    if c["cell_type"] == "code"
        src = join(c["source"])
        isempty(strip(src)) && continue
        Base.include_string(Main, src)
    end
end

println("DONE")

using JSON

nb_path = joinpath(@__DIR__, "lab_sa_berlin52.ipynb")
nb = JSON.parsefile(nb_path)

for c in nb["cells"]
    if c["cell_type"] == "code"
        src = join(c["source"])
        isempty(strip(src)) && continue
        Base.include_string(Main, src)
    end
end

println("DONE")

