package refal.runtime;

import org.junit.jupiter.api.Test;
import refal.ast.Br;
import refal.ast.EVar;
import refal.ast.Num;
import refal.ast.SVar;
import refal.ast.Sym;
import refal.ast.TVar;
import refal.ast.Term;

import refal.deque.Expr;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

class MatcherTest {

    private static List<Term> p(Term... ts) {
        return List.of(ts);
    }

    @Test
    void emptyMatchesEmpty() {
        Optional<Bindings> r = Matcher.match(List.of(), List.of());
        assertThat(r).isPresent();
        assertThat(r.get().asMap()).isEmpty();
    }

    @Test
    void emptyDoesNotMatchNonEmpty() {
        var r = Matcher.match(List.of(), p(new Sym("A")));
        assertThat(r).isEmpty();
    }

    @Test
    void singleSVariableBindsAtom() {
        var r = Matcher.match(
                p(new SVar("X")),
                p(new Sym("Hello")));
        assertThat(r).isPresent();
        assertThat(r.get().get("s.X")).containsExactly(new Sym("Hello"));
    }

    @Test
    void sVariableRejectsBracketTerm() {
        var r = Matcher.match(
                p(new SVar("X")),
                p(new Br(Expr.fromList(List.of(new Sym("A"))))));
        assertThat(r).isEmpty();
    }

    @Test
    void tVariableAcceptsBracketTerm() {
        var inner = new Br(Expr.fromList(List.of(new Sym("A"), new Sym("B"))));
        var r = Matcher.match(
                p(new TVar("X")),
                p(inner));
        assertThat(r).isPresent();
        assertThat(r.get().get("t.X")).containsExactly(inner);
    }

    @Test
    void eVariableMatchesEmptyAndAll() {
        var r = Matcher.match(
                p(new EVar("X")),
                List.of());
        assertThat(r).isPresent();
        assertThat(r.get().get("e.X")).isEmpty();

        var s = Matcher.match(
                p(new EVar("X")),
                p(new Sym("A"), new Sym("B"), new Sym("C")));
        assertThat(s).isPresent();
        assertThat(s.get().get("e.X")).containsExactly(
                new Sym("A"), new Sym("B"), new Sym("C"));
    }

    @Test
    void eVariableSplitsCorrectly() {
        var r = Matcher.match(
                p(new SVar("A"), new SVar("B"), new EVar("Rest")),
                p(new Sym("A"), new Sym("B"), new Sym("C"), new Sym("D"), new Sym("E")));
        assertThat(r).isPresent();
        assertThat(r.get().get("s.A")).containsExactly(new Sym("A"));
        assertThat(r.get().get("s.B")).containsExactly(new Sym("B"));
        assertThat(r.get().get("e.Rest")).containsExactly(
                new Sym("C"), new Sym("D"), new Sym("E"));
    }

    @Test
    void eVariableBacktracksToAdmitTrailingPattern() {
        var r = Matcher.match(
                p(new EVar("X"), new Sym("last")),
                p(new Sym("A"), new Sym("B"), new Sym("last")));
        assertThat(r).isPresent();
        assertThat(r.get().get("e.X")).containsExactly(new Sym("A"), new Sym("B"));
    }

    @Test
    void repeatedEVariable() {
        var r = Matcher.match(
                p(new EVar("X"), new EVar("X")),
                p(new Sym("A"), new Sym("B"), new Sym("A"), new Sym("B")));
        assertThat(r).isPresent();
        assertThat(r.get().get("e.X")).containsExactly(new Sym("A"), new Sym("B"));
    }

    @Test
    void repeatedEVariableNoMatch() {
        var r = Matcher.match(
                p(new EVar("X"), new EVar("X")),
                p(new Sym("A"), new Sym("B"), new Sym("C")));
        assertThat(r).isEmpty();
    }

    @Test
    void bracketedPatternMatchesBracket() {
        var r = Matcher.match(
                p(new Br(Expr.fromList(List.of(new SVar("X"), new SVar("Y"))))),
                p(new Br(Expr.fromList(List.of(new Sym("A"), new Sym("B"))))));
        assertThat(r).isPresent();
        assertThat(r.get().get("s.X")).containsExactly(new Sym("A"));
        assertThat(r.get().get("s.Y")).containsExactly(new Sym("B"));
    }

    @Test
    void bracketedPatternFailsAgainstFlat() {
        var r = Matcher.match(
                p(new Br(Expr.fromList(List.of(new Sym("A"))))),
                p(new Sym("A")));
        assertThat(r).isEmpty();
    }

    @Test
    void literalMatchesByEquality() {
        var r = Matcher.match(
                p(new Num(1), new Sym("A"), new Num(2)),
                p(new Num(1), new Sym("A"), new Num(2)));
        assertThat(r).isPresent();
    }

    @Test
    void repeatedSVariable() {
        var r = Matcher.match(
                p(new SVar("X"), new SVar("X")),
                p(new Sym("A"), new Sym("A")));
        assertThat(r).isPresent();

        var s = Matcher.match(
                p(new SVar("X"), new SVar("X")),
                p(new Sym("A"), new Sym("B")));
        assertThat(s).isEmpty();
    }
}
