package refal.deque;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class DeepDequeTest {

    private static List<Integer> seq(int n) {
        List<Integer> xs = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            xs.add(i);
        }
        return xs;
    }

    @Test
    void pushBackPromotesToDeepAtCapacityPlusOne() {
        Expr<Integer> d = Expr.empty();
        for (int i = 0; i < ShallowDeque.CAPACITY + 1; i++) {
            d = d.pushBack(i);
        }
        assertThat(d).isInstanceOf(DeepDeque.class);
        assertThat(d.size()).isEqualTo(ShallowDeque.CAPACITY + 1);
        assertThat(d.toList()).isEqualTo(seq(ShallowDeque.CAPACITY + 1));
    }

    @Test
    void pushFrontPromotesToDeepAtCapacityPlusOne() {
        Expr<Integer> d = Expr.empty();
        for (int i = 0; i < ShallowDeque.CAPACITY + 1; i++) {
            d = d.pushFront(i);
        }
        assertThat(d).isInstanceOf(DeepDeque.class);
        List<Integer> expected = new ArrayList<>();
        for (int i = ShallowDeque.CAPACITY; i >= 0; i--) {
            expected.add(i);
        }
        assertThat(d.toList()).isEqualTo(expected);
    }

    @Test
    void manyPushBackKeepsCorrectOrder() {
        int n = 1000;
        Expr<Integer> d = Expr.empty();
        for (int i = 0; i < n; i++) {
            d = d.pushBack(i);
        }
        assertThat(d.size()).isEqualTo(n);
        assertThat(d.toList()).isEqualTo(seq(n));
    }

    @Test
    void manyPushFrontReversesOrder() {
        int n = 500;
        Expr<Integer> d = Expr.empty();
        for (int i = 0; i < n; i++) {
            d = d.pushFront(i);
        }
        List<Integer> expected = new ArrayList<>();
        for (int i = n - 1; i >= 0; i--) {
            expected.add(i);
        }
        assertThat(d.toList()).isEqualTo(expected);
    }

    @Test
    void separateFrontTraversesAllElementsInOrder() {
        int n = 100;
        Expr<Integer> d = Expr.fromList(seq(n));
        List<Integer> got = new ArrayList<>();
        while (!d.isEmpty()) {
            var pr = d.separateFront();
            got.add(pr.term());
            d = pr.rest();
        }
        assertThat(got).isEqualTo(seq(n));
    }

    @Test
    void separateBackTraversesInReverse() {
        int n = 100;
        Expr<Integer> d = Expr.fromList(seq(n));
        List<Integer> got = new ArrayList<>();
        while (!d.isEmpty()) {
            var pr = d.separateBack();
            got.add(pr.term());
            d = pr.rest();
        }
        List<Integer> expected = new ArrayList<>();
        for (int i = n - 1; i >= 0; i--) {
            expected.add(i);
        }
        assertThat(got).isEqualTo(expected);
    }

    @Test
    void mkDeepCollapsesWhenSmallEnough() {
        // Строим Deep, затем снимаем элементы, пока size не упадёт до CAPACITY.
        int n = ShallowDeque.CAPACITY + 5;
        Expr<Integer> d = Expr.fromList(seq(n));
        assertThat(d).isInstanceOf(DeepDeque.class);
        for (int i = 0; i < 5; i++) {
            d = d.separateFront().rest();
        }
        // Сейчас size == CAPACITY → должен схлопнуться в Shallow.
        assertThat(d.size()).isEqualTo(ShallowDeque.CAPACITY);
        assertThat(d).isInstanceOf(ShallowDeque.class);
    }

    @Test
    void interleavedPushAndPopRoundtrip() {
        Expr<Integer> d = Expr.empty();
        for (int i = 0; i < 50; i++) {
            d = d.pushBack(i);
        }
        // Снимаем 30 элементов с начала
        for (int i = 0; i < 30; i++) {
            var pr = d.separateFront();
            assertThat(pr.term()).isEqualTo(i);
            d = pr.rest();
        }
        // Добавляем 100 элементов в начало
        for (int i = 0; i < 100; i++) {
            d = d.pushFront(-i);
        }
        // Итоговый размер: 50 - 30 + 100 = 120
        assertThat(d.size()).isEqualTo(120);
        // Первые 100 должны быть в обратном порядке: -0..-99 → -99..0
        List<Integer> result = d.toList();
        assertThat(result.get(0)).isEqualTo(-99);
        assertThat(result.get(99)).isEqualTo(0);
        assertThat(result.get(100)).isEqualTo(30);
        assertThat(result.get(119)).isEqualTo(49);
    }

    @Test
    void emptySeparateThrowsForBothEnds() {
        Expr<Integer> d = Expr.empty();
        assertThatThrownBy(d::separateFront).isInstanceOf(IllegalStateException.class);
        assertThatThrownBy(d::separateBack).isInstanceOf(IllegalStateException.class);
    }
}
