package refal.ast;

import java.math.BigInteger;

// Целое число (макроцифра Рефала-5). Произвольной точности.
public record Num(BigInteger value) implements Term {
    public Num(long v) {
        this(BigInteger.valueOf(v));
    }
}
