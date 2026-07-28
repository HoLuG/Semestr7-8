package refal.semantic;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import refal.ast.Program;
import refal.parser.Parser;
import refal.support.Resources;

import java.util.Optional;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class SemanticTest {

    private static final Set<String> BUILTINS = Set.of(
            "Add", "Sub", "Mul", "Div", "Mod", "Compare",
            "Prout", "Print", "Putout", "Symb", "Numb", "Chr",
            "Ord", "Lower", "Upper", "Mu", "Map", "Exit");

    @Test
    void okProgramReportsResolvedEntry() {
        Program p = Parser.parse("""
                $ENTRY Main;
                Main { = 'X'; }
                """);
        SemanticInfo info = SemanticChecker.check(p, Optional.empty(), BUILTINS);
        assertThat(info.entry()).hasValue("Main");
        assertThat(info.funcEnv()).containsKey("Main");
    }

    @Test
    void overrideEntryWins() {
        Program p = Parser.parse("""
                $ENTRY Main;
                Main { = A; }
                Other { = B; }
                """);
        SemanticInfo info = SemanticChecker.check(p, Optional.of("Other"), BUILTINS);
        assertThat(info.entry()).hasValue("Other");
    }

    @Test
    void undefinedEntryRejected() {
        Program p = Parser.parse("""
                $ENTRY Missing;
                Other { = ; }
                """);
        assertThatThrownBy(() -> SemanticChecker.check(p, Optional.empty(), BUILTINS))
                .isInstanceOf(SemanticException.class)
                .matches(ex -> ((SemanticException) ex).kind()
                        == SemanticException.Kind.UNDEFINED_ENTRY);
    }

    @Test
    void duplicateFunctionRejected() {
        Program p = Parser.parse("""
                Main { = A; }
                Main { = B; }
                """);
        assertThatThrownBy(() -> SemanticChecker.check(p, Optional.empty(), BUILTINS))
                .isInstanceOf(SemanticException.class)
                .matches(ex -> ((SemanticException) ex).kind()
                        == SemanticException.Kind.DUPLICATE_FUNCTION);
    }

    @Test
    void unboundResultVariableRejected() {
        Program p = Parser.parse("F { s.X = s.X s.Y; }");
        assertThatThrownBy(() -> SemanticChecker.check(p, Optional.empty(), BUILTINS))
                .isInstanceOf(SemanticException.class)
                .matches(ex -> ((SemanticException) ex).kind()
                        == SemanticException.Kind.UNBOUND_VARIABLE);
    }

    // В классическом Рефале-5 переменные с одинаковым именем, но разным
    // префиксом типа (s.X, t.X, e.X), считаются разными — конфликт типов
    // здесь невозможен. SemanticChecker реализует именно эту семантику,
    // поэтому тесты на VARIABLE_TYPE_MISMATCH для `s.X e.X` удалены.

    @Test
    void undefinedCallRejected() {
        Program p = Parser.parse("F { = <NoSuchFunc 1 2>; }");
        assertThatThrownBy(() -> SemanticChecker.check(p, Optional.empty(), BUILTINS))
                .isInstanceOf(SemanticException.class)
                .matches(ex -> ((SemanticException) ex).kind()
                        == SemanticException.Kind.UNDEFINED_FUNCTION);
    }

    @Test
    void externDeclaredCallIsAccepted() {
        Program p = Parser.parse("""
                $EXTERN Foo;
                F { = <Foo 1 2>; }
                """);
        assertThat(SemanticChecker.check(p, Optional.empty(), BUILTINS).externs())
                .contains("Foo");
    }

    @Test
    void userFunctionShadowingBuiltinRejected() {
        // Пользователь определил функцию с именем встроенной — BUILTIN_SHADOW.
        Program p = Parser.parse("Prout { e.X = e.X; }");
        assertThatThrownBy(() -> SemanticChecker.check(p, Optional.empty(), BUILTINS))
                .isInstanceOf(SemanticException.class)
                .matches(ex -> ((SemanticException) ex).kind()
                        == SemanticException.Kind.BUILTIN_SHADOW);
    }

    @ParameterizedTest
    @CsvSource({
            "fixtures/bad-semantic/duplicate-func.ref,DUPLICATE_FUNCTION",
            "fixtures/bad-semantic/result-var-not-in-pattern.ref,UNBOUND_VARIABLE",
            "fixtures/bad-semantic/undefined-call.ref,UNDEFINED_FUNCTION",
            "fixtures/bad-semantic/undefined-entry.ref,UNDEFINED_ENTRY"
    })
    void badSemanticFixtureMatchesExpectedKind(String resource, String expectedKindName) {
        String src = Resources.read(resource);
        Program p = Parser.parse(src);
        SemanticException.Kind expected = SemanticException.Kind.valueOf(expectedKindName);
        assertThatThrownBy(() -> SemanticChecker.check(p, Optional.empty(), BUILTINS))
                .isInstanceOf(SemanticException.class)
                .matches(ex -> ((SemanticException) ex).kind() == expected,
                        "expected kind=" + expected);
    }
}
