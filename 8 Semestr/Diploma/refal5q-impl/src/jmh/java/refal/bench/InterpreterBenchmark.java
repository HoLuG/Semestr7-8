package refal.bench;

import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Fork;
import org.openjdk.jmh.annotations.Measurement;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Param;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.Setup;
import org.openjdk.jmh.annotations.State;
import org.openjdk.jmh.annotations.Warmup;
import refal.ast.Num;
import refal.ast.Program;
import refal.ast.Term;
import refal.parser.Parser;
import refal.runtime.Runtime;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Бенчмарки интерпретатора на типичных программах
 */
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MILLISECONDS)
@Warmup(iterations = 3, time = 1, timeUnit = TimeUnit.SECONDS)
@Measurement(iterations = 5, time = 1, timeUnit = TimeUnit.SECONDS)
@Fork(1)
@State(Scope.Benchmark)
public class InterpreterBenchmark {

    @Param({"50", "200", "500"})
    public int n;

    private Program reverseProg;
    private Program appendProg;
    private List<Term> reverseInput;
    private List<Term> appendInput;

    @Setup
    public void setup() {
        reverseProg = Parser.parse("""
                Reverse {
                  = ;
                  s.X e.Rest = <Reverse e.Rest> s.X;
                }
                """);
        appendProg = Parser.parse("""
                Append {
                  (e.X) (e.Y) = e.X e.Y;
                }
                """);

        List<Term> ri = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            ri.add(new Num(i));
        }
        reverseInput = ri;

        List<Term> a = new ArrayList<>(n / 2);
        List<Term> b = new ArrayList<>(n / 2);
        for (int i = 0; i < n / 2; i++) {
            a.add(new Num(i));
            b.add(new Num(n / 2 + i));
        }
        appendInput = List.of(
                new refal.ast.Br(a),
                new refal.ast.Br(b));
    }

    @Benchmark
    public List<Term> reverse() {
        Runtime rt = new Runtime(reverseProg);
        return rt.run("Reverse", reverseInput);
    }

    @Benchmark
    public List<Term> append() {
        Runtime rt = new Runtime(appendProg);
        return rt.run("Append", appendInput);
    }
}
