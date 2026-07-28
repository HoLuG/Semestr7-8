package refal.deque;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class ConcatTest {

    private static List<Integer> seq(int from, int len) {
        List<Integer> xs = new ArrayList<>(len);
        for (int i = 0; i < len; i++) {
            xs.add(from + i);
        }
        return xs;
    }

    @Test
    void shallowPlusShallowFitsInOne() {
        Expr<Integer> a = Expr.fromList(List.of(1, 2, 3));
        Expr<Integer> b = Expr.fromList(List.of(4, 5));
        Expr<Integer> r = Expr.concat(a, b);
        assertThat(r.size()).isEqualTo(5);
        assertThat(r).isInstanceOf(ShallowDeque.class);
        assertThat(r.toList()).containsExactly(1, 2, 3, 4, 5);
    }

    @Test
    void shallowPlusShallowOverflowsToDeep() {
        Expr<Integer> a = Expr.fromList(seq(0, 7));
        Expr<Integer> b = Expr.fromList(seq(7, 7));
        Expr<Integer> r = Expr.concat(a, b);
        assertThat(r.size()).isEqualTo(14);
        assertThat(r).isInstanceOf(DeepDeque.class);
        assertThat(r.toList()).isEqualTo(seq(0, 14));
    }

    @Test
    void shallowPlusDeep() {
        Expr<Integer> a = Expr.fromList(seq(0, 4));
        Expr<Integer> b = Expr.fromList(seq(4, 30));
        assertThat(b).isInstanceOf(DeepDeque.class);

        Expr<Integer> r = Expr.concat(a, b);
        assertThat(r.size()).isEqualTo(34);
        assertThat(r.toList()).isEqualTo(seq(0, 34));
    }

    @Test
    void deepPlusShallow() {
        Expr<Integer> a = Expr.fromList(seq(0, 30));
        Expr<Integer> b = Expr.fromList(seq(30, 4));
        assertThat(a).isInstanceOf(DeepDeque.class);

        Expr<Integer> r = Expr.concat(a, b);
        assertThat(r.size()).isEqualTo(34);
        assertThat(r.toList()).isEqualTo(seq(0, 34));
    }

    @Test
    void deepPlusDeep() {
        Expr<Integer> a = Expr.fromList(seq(0, 50));
        Expr<Integer> b = Expr.fromList(seq(50, 50));
        assertThat(a).isInstanceOf(DeepDeque.class);
        assertThat(b).isInstanceOf(DeepDeque.class);

        Expr<Integer> r = Expr.concat(a, b);
        assertThat(r.size()).isEqualTo(100);
        assertThat(r.toList()).isEqualTo(seq(0, 100));
    }

    @Test
    void concatEmptyIsIdentity() {
        Expr<Integer> a = Expr.fromList(seq(0, 20));
        assertThat(Expr.concat(Expr.empty(), a)).isEqualTo(a);
        assertThat(Expr.concat(a, Expr.empty())).isEqualTo(a);
        assertThat(Expr.concat(Expr.<Integer>empty(), Expr.<Integer>empty())
                .isEmpty()).isTrue();
    }

    @Test
    void concatStressManyConcats() {
        Expr<Integer> r = Expr.empty();
        List<Integer> expected = new ArrayList<>();
        for (int chunk = 0; chunk < 100; chunk++) {
            int chunkSize = 13;
            List<Integer> piece = seq(chunk * chunkSize, chunkSize);
            expected.addAll(piece);
            r = Expr.concat(r, Expr.fromList(piece));
        }
        assertThat(r.size()).isEqualTo(expected.size());
        assertThat(r.toList()).isEqualTo(expected);
    }

    @Test
    void concatThenSeparateRoundtrip() {
        Expr<Integer> a = Expr.fromList(seq(0, 27));
        Expr<Integer> b = Expr.fromList(seq(27, 27));
        Expr<Integer> r = Expr.concat(a, b);

        List<Integer> got = new ArrayList<>();
        while (!r.isEmpty()) {
            var pr = r.separateFront();
            got.add(pr.term());
            r = pr.rest();
        }
        assertThat(got).isEqualTo(seq(0, 54));
    }

    @Test
    void singletonAndEmpty() {
        Expr<String> s = Expr.singleton("X");
        assertThat(s.size()).isEqualTo(1);
        assertThat(s.toList()).containsExactly("X");
        assertThat(Expr.<String>empty().isEmpty()).isTrue();
    }
}
