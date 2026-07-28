package refal.bench;

import org.openjdk.jmh.Main;

/**
 * Точка входа для JMH-бенчмарков.
 */
public final class BenchmarkRunner {
    private BenchmarkRunner() {
    }

    public static void main(String[] args) throws Exception {
        Main.main(args);
    }
}
