package refal;

import org.junit.jupiter.api.Assumptions;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.stream.Stream;

/**
 * Прогон интеграционных тестов из refal-5j/autotests/ и рассахаренных тестов
 * из refal-5-framework-master/bin/desugared_tests/.
 */
class AutotestsRunnerTest {

    // ---- Лимиты и таймауты --------------------------------------------------

    private static final int DEFAULT_STEP_LIMIT = 5_000_000;

    /** Максимальное время ожидания одного теста (секунды). */
    private static final int TEST_TIMEOUT_SEC = 20;

    /**
     * Индивидуальные лимиты для «тяжёлых» тестов.
     * Тест 20-time-timeelapsed.ref пропускается (144с из-за O(n^6) backtracking).
     */
    private static final Map<String, Integer> STEP_LIMITS = Map.of(
            "03-concat.ref", 20_000_000
    );

    /**
     * Тесты из refal-5j/autotests/, которые должны проходить обязательно
     */
    private static final Set<String> MUST_PASS = Set.of(
            "01-go.ref",
            "02-matches.ref",
            "03-concat.ref",
            "09-1-mu-uses-all.ref",
            "09-2-mu.ref"
    );

    /**
     * Тесты из refal-5j/autotests/, которые пропускаем (слишком медленные
     * или требуют специальных условий).
     */
    private static final Set<String> SKIP_TESTS = Set.of(
            "20-time-timeelapsed.ref" // O(n^6) backtracking
    );

    /**
     * Тесты из desugared_tests/, которые пропускаем (читают stdin, создают
     * файлы с побочными эффектами или запускают внешние процессы).
     */
    private static final Set<String> SKIP_DESUGARED = Set.of(
            "Get-0-stdin.OK_d.ref",   // читает из stdin — блокирует
            "Card.OK_d.ref",          // Card читает stdin
            "Get-autoopen.OK_d.ref",  // автооткрытие REFALNN.DAT (побочный эффект)
            "RemoveFile.OK_d.ref",    // удаляет файлы на диске
            "System-1-echo.OK_d.ref", // запускает внешний процесс
            "System-2-Exit-retcode.OK_d.ref" // <Exit N> — ожидаем ExitSignal
    );

    /**
     * Тесты из desugared_tests/, которые должны проходить обязательно.
     * Остальные записываются в статистику, но не бросают AssertionError —
     * они могут использовать нереализованные built-in функции (Time, SizeOf,
     * GetEnv, Random, Br/Cp/Dg и т.д.), которые выходят за рамки базисного
     * подмножества Рефала-5.
     */
    private static final Set<String> MUST_PASS_DESUGARED = Set.of(
            "1-Prout.OK_d.ref",
            "Add-Numb-Symb.OK_d.ref",
            "Chr-Lower-Ord-Upper.OK_d.ref",
            "Compare.OK_d.ref",
            "Divmod-Numb-Symb.OK_d.ref",
            "Div-Numb-Symb.OK_d.ref",
            "Explode.OK_d.ref",
            "fact.OK_d.ref",
            "First-Last-Lenw.OK_d.ref",
            "GO.OK_d.ref",
            "Go-GO.OK_d.ref",
            "Implode-Implode_Ext.OK_d.ref",
            "math-sign.OK_d.ref",
            "Mod-Numb-Symb.OK_d.ref",
            "Mul-Numb-Symb.OK_d.ref",
            "Numb-Symb.OK_d.ref",
            "Sub.OK_d.ref",
            "Type.OK_d.ref"
    );

    /**
     * Тесты, которым нужен satellite-файл из подпапки satellite/.
     * Значение — relative path к satellite файлу от autotests/.
     */
    private static final Map<String, String> SATELLITE_FILES = Map.of(
            "09-1-mu-uses-all.ref", "satellite/09-1-mu-uses-all.ref",
            "09-2-mu.ref",          "satellite/09-2-mu.ref"
    );

    // ---- Прогон refal-5j autotests --------------------------------------

    @TestFactory
    Stream<DynamicTest> refal5jAutotests() throws IOException {
        Path dir = locateAutotestsDir();
        Assumptions.assumeTrue(dir != null,
                "refal-5j autotests directory not found — skipping suite");

        List<Path> files;
        try (Stream<Path> s = Files.list(dir)) {
            files = s.filter(p -> p.getFileName().toString().endsWith(".ref"))
                    .sorted()
                    .toList();
        }

        List<TestRecord> records = new ArrayList<>();
        List<DynamicTest> tests = new ArrayList<>();

        for (Path file : files) {
            String name = file.getFileName().toString();
            tests.add(DynamicTest.dynamicTest(name, () -> {
                if (SKIP_TESTS.contains(name)) {
                    records.add(new TestRecord(name, "SKIP", "known slow (O(n^6) backtracking)", 0, 0));
                    Assumptions.abort("skipping known-slow test: " + name);
                    return;
                }
                int stepLimit = STEP_LIMITS.getOrDefault(name, DEFAULT_STEP_LIMIT);
                String fileArg = buildFileArg(dir, name);
                TestRecord rec = runTest(name, fileArg, stepLimit);
                records.add(rec);
                // Жёсткий FAIL только для тестов из белого списка.
                // Остальные могут не проходить (расширенный синтаксис, нереализованные функции).
                if (rec.status().startsWith("FAIL") && MUST_PASS.contains(name)) {
                    throw new AssertionError(name + " failed: " + rec.detail());
                }
            }));
        }

        tests.add(DynamicTest.dynamicTest("=summary=", () -> {
            String report = buildReport("refal-5j autotests", records, files.size());
            System.out.println(report);
            saveReport(report, "refal-5j autotests");
        }));

        return tests.stream();
    }

    // ---- Прогон рассахаренных тестов ------------------------------------

    @TestFactory
    Stream<DynamicTest> desugaredTests() throws IOException {
        Path dir = locateDesugaredDir();
        Assumptions.assumeTrue(dir != null,
                "desugared_tests directory not found — skipping suite");

        List<Path> files;
        try (Stream<Path> s = Files.list(dir)) {
            files = s.filter(p -> p.getFileName().toString().endsWith(".OK_d.ref"))
                    .sorted()
                    .toList();
        }

        List<TestRecord> records = new ArrayList<>();
        List<DynamicTest> tests = new ArrayList<>();

        for (Path file : files) {
            String name = file.getFileName().toString();
            tests.add(DynamicTest.dynamicTest(name, () -> {
                if (SKIP_DESUGARED.contains(name)) {
                    records.add(new TestRecord(name, "SKIP", "known problematic (stdin/side effects)", 0, 0));
                    Assumptions.abort("skipping: " + name);
                    return;
                }
                TestRecord rec = runTest(name, file.toAbsolutePath().toString(), DEFAULT_STEP_LIMIT);
                records.add(rec);
                // Жёсткий FAIL только для тестов базисного подмножества.
                // Остальные могут не проходить (нереализованные built-in: Time, SizeOf, GetEnv, ...).
                if (rec.status().startsWith("FAIL") && MUST_PASS_DESUGARED.contains(name)) {
                    throw new AssertionError(name + " failed: " + rec.detail());
                }
            }));
        }

        tests.add(DynamicTest.dynamicTest("=summary=", () -> {
            String report = buildReport("desugared tests", records, files.size());
            System.out.println(report);
            saveReport(report, "desugared tests");
        }));

        return tests.stream();
    }

    // ---- Вспомогательные методы -----------------------------------------

    private String buildFileArg(Path autotestsDir, String name) {
        String mainPath = autotestsDir.resolve(name).toAbsolutePath().toString();
        String satelliteRelative = SATELLITE_FILES.get(name);
        if (satelliteRelative != null) {
            String satPath = autotestsDir.resolve(satelliteRelative).toAbsolutePath().toString();
            return mainPath + "+" + satPath;
        }
        return mainPath;
    }

    private TestRecord runTest(String name, String fileArg, int stepLimit) {
        long startMs = System.currentTimeMillis();
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        ByteArrayOutputStream err = new ByteArrayOutputStream();
        PrintStream outPs = new PrintStream(out, true, StandardCharsets.UTF_8);
        PrintStream errPs = new PrintStream(err, true, StandardCharsets.UTF_8);
        String[] args = new String[]{fileArg, "--step-limit", String.valueOf(stepLimit)};

        ExecutorService exec = Executors.newSingleThreadExecutor();
        Future<Integer> future = exec.submit(() -> Main.run(args, outPs, errPs));
        int code;
        try {
            code = future.get(TEST_TIMEOUT_SEC, TimeUnit.SECONDS);
        } catch (TimeoutException e) {
            future.cancel(true);
            exec.shutdownNow();
            long ms = System.currentTimeMillis() - startMs;
            return new TestRecord(name, "FAIL(timeout>" + TEST_TIMEOUT_SEC + "s)",
                    "test exceeded " + TEST_TIMEOUT_SEC + "s (stdin block or infinite loop?)", stepLimit, ms);
        } catch (Exception e) {
            long ms = System.currentTimeMillis() - startMs;
            return new TestRecord(name, "FAIL(exception)",
                    e.getCause() != null ? e.getCause().getMessage() : e.getMessage(), stepLimit, ms);
        } finally {
            exec.shutdownNow();
        }
        long ms = System.currentTimeMillis() - startMs;
        String errText = err.toString(StandardCharsets.UTF_8).trim();
        if (code == 0) {
            return new TestRecord(name, "PASS", out.toString(StandardCharsets.UTF_8).trim(), stepLimit, ms);
        } else {
            String detail = errText.isEmpty() ? "exit " + code : errText;
            if (detail.length() > 200) {
                detail = detail.substring(0, 197) + "...";
            }
            return new TestRecord(name, "FAIL(exit=" + code + ")", detail, stepLimit, ms);
        }
    }

    private String buildReport(String suite, List<TestRecord> records, int total) {
        long passed = records.stream().filter(r -> r.status().equals("PASS")).count();
        long failed = records.stream().filter(r -> r.status().startsWith("FAIL")).count();
        long skipped = records.stream().filter(r -> r.status().equals("SKIP")).count();

        StringBuilder sb = new StringBuilder();
        sb.append("## ").append(suite).append(" (").append(total).append(" tests) — ")
                .append(LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm")))
                .append("\n\n");
        sb.append("| Test | Status | Time |\n");
        sb.append("|------|--------|------|\n");
        for (TestRecord r : records) {
            String emoji = switch (r.status()) {
                case "PASS" -> "✅";
                case "SKIP" -> "⚠️";
                default -> "❌";
            };
            sb.append(String.format("| %s | %s %s | %dms |\n",
                    r.name(), emoji, r.status(), r.timeMs()));
        }
        sb.append("\n**Summary**: ").append(passed).append(" passed, ")
                .append(failed).append(" failed, ")
                .append(skipped).append(" skipped / ").append(total).append(" total\n");

        if (failed > 0) {
            sb.append("\n### Failed tests\n");
            records.stream()
                    .filter(r -> r.status().startsWith("FAIL"))
                    .forEach(r -> sb.append("- **").append(r.name()).append("**: ").append(r.detail()).append("\n"));
        }
        return sb.toString();
    }

    private void saveReport(String section, String suiteName) {
        Path benchDir = findBenchDir();
        if (benchDir == null) {
            System.err.println("bench/ directory not found — not saving AUTOTEST_RESULTS.md");
            return;
        }
        Path resultsFile = benchDir.resolve("AUTOTEST_RESULTS.md");
        try {
            String header = "# Autotest Results\n\nGenerated automatically by AutotestsRunnerTest.\n\n";
            String content;
            if (Files.exists(resultsFile)) {
                content = Files.readString(resultsFile, StandardCharsets.UTF_8);
                // Заменить секцию для данного suite или добавить в конец.
                // Маркер = точное начало заголовка ("## refal-5j autotests" или "## desugared tests").
                String marker = "## " + suiteName;
                int idx = content.indexOf(marker);
                if (idx >= 0) {
                    // Найти конец секции (следующую ## или конец файла)
                    int nextSection = content.indexOf("\n## ", idx + 1);
                    if (nextSection < 0) {
                        content = content.substring(0, idx) + section;
                    } else {
                        content = content.substring(0, idx) + section + "\n" + content.substring(nextSection + 1);
                    }
                } else {
                    content = content + "\n" + section;
                }
            } else {
                content = header + section;
            }
            Files.writeString(resultsFile, content, StandardCharsets.UTF_8);
            System.out.println("Results saved to: " + resultsFile);
        } catch (IOException e) {
            System.err.println("Could not save results: " + e.getMessage());
        }
    }

    // ---- Поиск директорий -----------------------------------------------

    private static Path locateAutotestsDir() {
        Path[] candidates = {
            Paths.get("tests", "autotests"),
            Paths.get("..", "refal-5j", "autotests"),
            Paths.get("d:", "Programming", "Projects", "8 Semestr", "Diploma", "refal-5j", "autotests"),
        };
        for (Path p : candidates) {
            if (Files.isDirectory(p)) {
                return p;
            }
        }
        return null;
    }

    private static Path locateDesugaredDir() {
        Path[] candidates = {
            Paths.get("tests", "desugared"),
            Paths.get("..", "refal-5-framework-master", "bin", "desugared_tests"),
            Paths.get("d:", "Programming", "Projects", "8 Semestr", "Diploma",
                      "refal-5-framework-master", "bin", "desugared_tests"),
        };
        for (Path p : candidates) {
            if (Files.isDirectory(p)) {
                return p;
            }
        }
        return null;
    }

    private static Path findBenchDir() {
        Path[] candidates = {
            Paths.get("bench"),
            Paths.get("..", "refal5j-impl", "bench"),
        };
        for (Path p : candidates) {
            if (Files.isDirectory(p)) {
                return p;
            }
        }
        return null;
    }

    // ---- Запись результата ----------------------------------------------

    private record TestRecord(String name, String status, String detail, int stepLimit, long timeMs) {
    }
}
