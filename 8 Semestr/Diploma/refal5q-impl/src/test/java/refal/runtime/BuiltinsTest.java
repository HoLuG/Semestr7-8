package refal.runtime;

import org.junit.jupiter.api.Test;
import refal.ast.Num;
import refal.ast.Program;
import refal.ast.Str;
import refal.ast.Sym;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class BuiltinsTest {

    private static Runtime emptyRt() {
        Program prog = Program.builder().build();
        return new Runtime(prog);
    }

    @Test
    void addSubMulDivMod() {
        var rt = emptyRt();
        assertThat(rt.evalCall("Add", List.of(new Num(2), new Num(3))).toList())
                .containsExactly(new Num(5));
        assertThat(rt.evalCall("Sub", List.of(new Num(10), new Num(3))).toList())
                .containsExactly(new Num(7));
        assertThat(rt.evalCall("Mul", List.of(new Num(4), new Num(6))).toList())
                .containsExactly(new Num(24));
        assertThat(rt.evalCall("Div", List.of(new Num(10), new Num(3))).toList())
                .containsExactly(new Num(3));
        assertThat(rt.evalCall("Mod", List.of(new Num(10), new Num(3))).toList())
                .containsExactly(new Num(1));
    }

    @Test
    void compareReturnsMacrocharacter() {
        var rt = emptyRt();
        assertThat(rt.evalCall("Compare", List.of(new Num(1), new Num(2))).toList())
                .containsExactly(new Str("-"));
        assertThat(rt.evalCall("Compare", List.of(new Num(5), new Num(5))).toList())
                .containsExactly(new Str("0"));
        assertThat(rt.evalCall("Compare", List.of(new Num(7), new Num(2))).toList())
                .containsExactly(new Str("+"));
    }

    @Test
    void divisionByZeroThrows() {
        var rt = emptyRt();
        assertThatThrownBy(() ->
                rt.evalCall("Div", List.of(new Num(1), new Num(0))))
                .isInstanceOf(RefalException.class);
        assertThatThrownBy(() ->
                rt.evalCall("Mod", List.of(new Num(1), new Num(0))))
                .isInstanceOf(RefalException.class);
    }

    @Test
    void prouAndPutoutAccumulateStdout() {
        var rt = emptyRt();
        // Sym → "hello " (с пробелом после слова), Prout добавляет '\n'
        rt.evalCall("Prout", List.of(new Sym("hello")));
        // Str → без пробела, Putout без канала → stdout без '\n'
        rt.evalCall("Putout", List.of(new Str(", world")));
        assertThat(rt.stdout()).isEqualTo("hello \n, world");
    }

    @Test
    void symbReturnsEmptyOnEmptyInput() {
        var rt = emptyRt();
        assertThat(rt.evalCall("Symb", List.of()).toList()).isEmpty();
    }

    @Test
    void numbParsesLeadingInteger() {
        var rt = emptyRt();
        assertThat(rt.evalCall("Numb", List.of(new Str("42"))).toList())
                .containsExactly(new Num(42));
        assertThat(rt.evalCall("Numb", List.of(new Str("-17"))).toList())
                .containsExactly(new Str("-"), new Num(17));
        // Невалидный вход — возвращаем 0 (поведение refgo), а не исключение.
        assertThat(rt.evalCall("Numb", List.of(new Str("abc"))).toList())
                .containsExactly(new Num(0));
    }

    @Test
    void chrAndOrdRoundtrip() {
        var rt = emptyRt();
        assertThat(rt.evalCall("Chr", List.of(new Num('A'))).toList())
                .containsExactly(new Str("A"));
        assertThat(rt.evalCall("Ord", List.of(new Str("Z"))).toList())
                .containsExactly(new Num('Z'));
    }

    @Test
    void lowerUpper() {
        var rt = emptyRt();
        assertThat(rt.evalCall("Lower", List.of(new Str("HELLO"))).toList())
                .containsExactly(new Str("hello"));
        assertThat(rt.evalCall("Upper", List.of(new Str("hello"))).toList())
                .containsExactly(new Str("HELLO"));
    }

    @Test
    void exitTranslatesToSignal() {
        var rt = emptyRt();
        assertThatThrownBy(() ->
                rt.evalCall("Exit", List.of(new Num(7))))
                .isInstanceOf(Builtins.ExitSignal.class)
                .matches(ex -> ((Builtins.ExitSignal) ex).code() == 7);
    }

    @Test
    void muCallsUserFunction() {
        // Пользовательская функция Inc увеличивает аргумент на 1; Mu должна
        // вызвать её и полностью нормализовать результат до 6.
        Program prog = refal.parser.Parser.parse("""
                $ENTRY Test;
                Inc { s.X = <Add s.X 1>; }
                Test { = <Mu Inc 5>; }
                """);
        Runtime rt = new Runtime(prog);
        refal.semantic.SemanticChecker.check(
                prog, Optional.empty(), rt.builtinNames());

        var out = rt.run("Inc", List.of(new Num(5)));
        assertThat(out).containsExactly(new Num(6));

        var muOut = rt.run("Test", List.of());
        assertThat(muOut).containsExactly(new Num(6));
    }
}
