package refal.runtime;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;
import refal.ast.AstFormatter;
import refal.ast.Program;
import refal.ast.Term;
import refal.parser.Parser;
import refal.semantic.SemanticChecker;
import refal.support.Resources;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Stream;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Чёрный ящик: на каждой фикстуре из fixtures/ok/ и
 * fixtures/desugared/ прогоняем полный пайплайн (лексер → парсер →
 * семантика → интерпретатор) и сравниваем результат с эталоном из
 * соответствующего expected.json
 */
class RuntimeIntegrationTest {
    /**
     * Каждая запись: путь к ресурсу, входное выражение, ожидаемый текстовый
     * результат.
     */
    record Fixture(String resource, String inputExpr, String expectedResult) {
    }

    private static Stream<Fixture> fixtures() {
        Map<String, String[]> ok = new LinkedHashMap<>();
        ok.put("hello.ref",        new String[]{"",            "'H' 'e' 'l' 'l' 'o'"});
        ok.put("swap.ref",         new String[]{"A B",         "B A"});
        ok.put("calls.ref",        new String[]{"",            "(A B)"});
        ok.put("brackets.ref",     new String[]{"",            "((A B (C)) (A B (C)))"});
        ok.put("vars_ste.ref",     new String[]{"A (B C) D E F", "D E F (B C) A"});
        ok.put("strings.ref",      new String[]{"",            "'c' 'o' 'u' 'n' 't' '=' '4' '2'"});
        ok.put("recursion.ref",    new String[]{"",            "5 4 3 2 1"});
        ok.put("repeated_var.ref", new String[]{"",            "(A B)"});
        ok.put("arith.ref",        new String[]{"",            "14"});
        ok.put("extern_noop.ref",  new String[]{"",            "Done"});

        Map<String, String[]> desugared = new LinkedHashMap<>();
        desugared.put("reverse-out.ref", new String[]{"", "10 9 8 7 6 5 4 3 2 1"});
        desugared.put("append-out.ref",  new String[]{"", "1 2 3 4 5 6"});

        return Stream.concat(
                ok.entrySet().stream().map(e -> new Fixture(
                        "fixtures/ok/" + e.getKey(),
                        e.getValue()[0], e.getValue()[1])),
                desugared.entrySet().stream().map(e -> new Fixture(
                        "fixtures/desugared/" + e.getKey(),
                        e.getValue()[0], e.getValue()[1])));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("fixtures")
    void fixtureMatchesExpected(Fixture fx) {
        String src = Resources.read(fx.resource);
        Program prog = Parser.parse(src);
        Runtime rt = new Runtime(prog);
        SemanticChecker.check(prog, Optional.empty(), rt.builtinNames());

        List<Term> initial = fx.inputExpr.isEmpty()
                ? List.of()
                : Parser.parseTerms(fx.inputExpr);
        String entry = prog.entry().orElseThrow();

        List<Term> result = rt.run(entry, initial);
        assertThat(AstFormatter.format(result)).isEqualTo(fx.expectedResult);
    }
}
