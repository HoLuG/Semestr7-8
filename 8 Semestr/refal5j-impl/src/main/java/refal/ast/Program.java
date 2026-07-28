package refal.ast;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

// Полная программа: набор функций, список $EXTERN, точка входа $ENTRY,
// и список имён функций, объявленных более одного раза (для проверки на дубли).
public record Program(
        Map<String, Func> funcs,
        Optional<String> entry,
        Set<String> externs,
        Set<String> duplicateFuncNames) {

    public Program {
        Objects.requireNonNull(funcs, "Program.funcs");
        Objects.requireNonNull(entry, "Program.entry");
        Objects.requireNonNull(externs, "Program.externs");
        Objects.requireNonNull(duplicateFuncNames, "Program.duplicateFuncNames");
        // Map.copyOf не гарантирует порядок итерации; нам важен порядок
        // объявления функций (для $ENTRY-резолвера и для повторяемых тестов).
        funcs = Collections.unmodifiableMap(new LinkedHashMap<>(funcs));
        externs = Collections.unmodifiableSet(new LinkedHashSet<>(externs));
        duplicateFuncNames = Collections.unmodifiableSet(new LinkedHashSet<>(duplicateFuncNames));
    }

    public static Builder builder() {
        return new Builder();
    }

    public Optional<Func> getFunc(String name) {
        return Optional.ofNullable(funcs.get(name));
    }

    // Вспомогательный класс для пошаговой сборки программы парсером.
    public static final class Builder {
        private final LinkedHashMap<String, Func> funcs = new LinkedHashMap<>();
        private final java.util.LinkedHashSet<String> externs = new java.util.LinkedHashSet<>();
        private final java.util.LinkedHashSet<String> duplicates = new java.util.LinkedHashSet<>();
        private String entry;

        private Builder() {
        }

        public Builder addFunc(Func f) {
            if (funcs.containsKey(f.name())) {
                duplicates.add(f.name());
            }
            funcs.put(f.name(), f);
            return this;
        }

        public boolean hasFunc(String name) {
            return funcs.containsKey(name);
        }

        public Builder addExterns(List<String> names) {
            externs.addAll(names);
            return this;
        }

        public Builder entry(String name) {
            this.entry = name;
            return this;
        }

        public String entryOrNull() {
            return entry;
        }

        public Program build() {
            return new Program(
                    funcs,
                    Optional.ofNullable(entry),
                    externs,
                    duplicates);
        }
    }
}
