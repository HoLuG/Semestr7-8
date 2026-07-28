package refal;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;

class MainTest {

    @Test
    void runsHelloRef(@TempDir Path tmp) throws Exception {
        Path src = tmp.resolve("hello.ref");
        Files.writeString(src, """
                $ENTRY Main;
                Main { = 'Hello'; }
                """);
        Captured out = run(src.toString());
        assertThat(out.exit).isZero();
        assertThat(out.stdout).contains("'H' 'e' 'l' 'l' 'o'");
    }

    @Test
    void runsWithExpr(@TempDir Path tmp) throws Exception {
        Path src = tmp.resolve("swap.ref");
        Files.writeString(src, """
                $ENTRY Main;
                Main { s.A s.B = s.B s.A; }
                """);
        Captured out = run(src.toString(), "--expr", "A B");
        assertThat(out.exit).isZero();
        assertThat(out.stdout.trim()).isEqualTo("B A");
    }

    @Test
    void overridesEntry(@TempDir Path tmp) throws Exception {
        Path src = tmp.resolve("two.ref");
        Files.writeString(src, """
                $ENTRY Main;
                Main { = M; }
                Other { = O; }
                """);
        Captured out = run(src.toString(), "--entry", "Other");
        assertThat(out.exit).isZero();
        assertThat(out.stdout.trim()).isEqualTo("O");
    }

    @Test
    void parseErrorReturns1(@TempDir Path tmp) throws Exception {
        Path src = tmp.resolve("bad.ref");
        Files.writeString(src, "F { = (");
        Captured out = run(src.toString());
        assertThat(out.exit).isEqualTo(1);
        assertThat(out.stderr).contains("[ERROR]");
    }

    @Test
    void semanticErrorReturns1(@TempDir Path tmp) throws Exception {
        Path src = tmp.resolve("bad.ref");
        Files.writeString(src, """
                F { s.X = s.Y; }
                """);
        Captured out = run(src.toString(), "--entry", "F", "--expr", "A");
        assertThat(out.exit).isEqualTo(1);
        assertThat(out.stderr).contains("[ERROR]");
    }

    @Test
    void runtimeErrorReturns2(@TempDir Path tmp) throws Exception {
        Path src = tmp.resolve("bad.ref");
        Files.writeString(src, """
                $ENTRY Main;
                Main { = <Div 1 0>; }
                """);
        Captured out = run(src.toString());
        assertThat(out.exit).isEqualTo(2);
    }

    @Test
    void stepLimitTriggersError(@TempDir Path tmp) throws Exception {
        Path src = tmp.resolve("loop.ref");
        Files.writeString(src, """
                $ENTRY Main;
                Main { = <Main>; }
                """);
        Captured out = run(src.toString(), "--step-limit", "10");
        assertThat(out.exit).isEqualTo(2);
    }

    @Test
    void exitBuiltinPropagatesCode(@TempDir Path tmp) throws Exception {
        Path src = tmp.resolve("ex.ref");
        Files.writeString(src, """
                $ENTRY Main;
                Main { = <Exit 7>; }
                """);
        Captured out = run(src.toString());
        assertThat(out.exit).isEqualTo(7);
    }

    @Test
    void usageOnNoArgs() {
        Captured out = run();
        assertThat(out.exit).isZero();
        assertThat(out.stdout).contains("usage:");
    }

    @Test
    void unknownFileReports1() {
        Captured out = run("nonexistent.ref");
        assertThat(out.exit).isEqualTo(1);
        assertThat(out.stderr).contains("cannot read");
    }

    private record Captured(int exit, String stdout, String stderr) {
    }

    private static Captured run(String... args) {
        ByteArrayOutputStream o = new ByteArrayOutputStream();
        ByteArrayOutputStream e = new ByteArrayOutputStream();
        int code = Main.run(args,
                new PrintStream(o, true, StandardCharsets.UTF_8),
                new PrintStream(e, true, StandardCharsets.UTF_8));
        return new Captured(code,
                o.toString(StandardCharsets.UTF_8),
                e.toString(StandardCharsets.UTF_8));
    }
}
