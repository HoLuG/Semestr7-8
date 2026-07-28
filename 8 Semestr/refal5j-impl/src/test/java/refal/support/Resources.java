package refal.support;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.util.Objects;

/**
 * Утилита для чтения ресурсов из src/test/resources/ в тестах
 */
public final class Resources {
    private Resources() {
    }
    /** Прочитать ресурс по пути относительно корня classpath, в UTF-8. */
    public static String read(String path) {
        try (var is = Objects.requireNonNull(
                Resources.class.getClassLoader().getResourceAsStream(path),
                "missing resource: " + path)) {
            return new String(is.readAllBytes(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
