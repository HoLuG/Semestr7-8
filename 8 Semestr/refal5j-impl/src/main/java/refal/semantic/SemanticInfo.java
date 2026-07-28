package refal.semantic;

import refal.ast.Func;

import java.util.Map;
import java.util.Optional;
import java.util.Set;

// Результат семантического анализа: функции, внешние имена, точка входа.
public record SemanticInfo(
        Map<String, Func> funcEnv,
        Set<String> externs,
        Optional<String> entry,
        Set<String> builtinNames) {

    public SemanticInfo {
        funcEnv = Map.copyOf(funcEnv);
        externs = Set.copyOf(externs);
        builtinNames = Set.copyOf(builtinNames);
    }
}
