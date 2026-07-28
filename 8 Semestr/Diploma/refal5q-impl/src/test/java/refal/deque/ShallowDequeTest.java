package refal.deque;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ShallowDequeTest {

    @Test
    void emptyHasZeroSize() {
        ShallowDeque<String> d = ShallowDeque.empty();
        assertThat(d.isEmpty()).isTrue();
        assertThat(d.size()).isZero();
        assertThat(d.iterator().hasNext()).isFalse();
        assertThat(d.toList()).isEmpty();
    }

    @Test
    void pushBackPreservesOrder() {
        ShallowDeque<String> d = ShallowDeque.<String>empty()
                .pushBackTight("A").pushBackTight("B").pushBackTight("C");
        assertThat(d.size()).isEqualTo(3);
        assertThat(d.toList()).containsExactly("A", "B", "C");
        assertThat(d.get(0)).isEqualTo("A");
        assertThat(d.get(2)).isEqualTo("C");
    }

    @Test
    void pushFrontPrependsInReverse() {
        ShallowDeque<String> d = ShallowDeque.<String>empty()
                .pushFrontTight("A").pushFrontTight("B").pushFrontTight("C");
        assertThat(d.toList()).containsExactly("C", "B", "A");
    }

    @Test
    void mixedPushAndCircularIndex() {
        ShallowDeque<Integer> d = ShallowDeque.empty();
        for (int i = 0; i < 5; i++) {
            d = d.pushBackTight(i);
        }
        for (int i = 1; i <= 3; i++) {
            d = d.pushFrontTight(-i);
        }
        assertThat(d.toList()).containsExactly(-3, -2, -1, 0, 1, 2, 3, 4);
    }

    @Test
    void separateFrontReturnsTermAndShorterRest() {
        ShallowDeque<String> d = ShallowDeque.<String>empty()
                .pushBackTight("A").pushBackTight("B").pushBackTight("C");
        var pr = d.separateFront();
        assertThat(pr.term()).isEqualTo("A");
        assertThat(pr.rest().size()).isEqualTo(2);
        assertThat(pr.rest().toList()).containsExactly("B", "C");
        assertThat(d.size()).isEqualTo(3);
    }

    @Test
    void separateBackReturnsTailTermAndShorterRest() {
        ShallowDeque<String> d = ShallowDeque.<String>empty()
                .pushBackTight("A").pushBackTight("B").pushBackTight("C");
        var pr = d.separateBack();
        assertThat(pr.term()).isEqualTo("C");
        assertThat(pr.rest().toList()).containsExactly("A", "B");
    }

    @Test
    void separateFromEmptyThrows() {
        assertThatThrownBy(() -> ShallowDeque.empty().separateFront())
                .isInstanceOf(IllegalStateException.class);
        assertThatThrownBy(() -> ShallowDeque.empty().separateBack())
                .isInstanceOf(IllegalStateException.class);
    }

    @Test
    void tightOverflowThrows() {
        ShallowDeque<Integer> d = ShallowDeque.empty();
        for (int i = 0; i < ShallowDeque.CAPACITY; i++) {
            d = d.pushBackTight(i);
        }
        assertThat(d.isFull()).isTrue();
        ShallowDeque<Integer> finalD = d;
        assertThatThrownBy(() -> finalD.pushBackTight(99))
                .isInstanceOf(IllegalStateException.class);
        assertThatThrownBy(() -> finalD.pushFrontTight(99))
                .isInstanceOf(IllegalStateException.class);
    }

    @Test
    void publicPushBackPromotesToDeepOnOverflow() {
        Expr<Integer> d = ShallowDeque.empty();
        for (int i = 0; i < ShallowDeque.CAPACITY; i++) {
            d = d.pushBack(i);
        }
        assertThat(d).isInstanceOf(ShallowDeque.class);

        d = d.pushBack(ShallowDeque.CAPACITY);
        assertThat(d).isInstanceOf(DeepDeque.class);
        assertThat(d.size()).isEqualTo(ShallowDeque.CAPACITY + 1);
    }

    @Test
    void immutabilityOriginalNotChanged() {
        ShallowDeque<String> d0 = ShallowDeque.<String>empty().pushBackTight("A");
        ShallowDeque<String> d1 = d0.pushBackTight("B");
        assertThat(d0.toList()).containsExactly("A");
        assertThat(d1.toList()).containsExactly("A", "B");
    }

    @Test
    void wrapAroundIndexingIsCorrect() {
        ShallowDeque<Integer> d = ShallowDeque.empty();
        for (int i = 0; i < 4; i++) {
            d = d.pushFrontTight(i);
        }
        for (int i = 100; i < 105; i++) {
            d = d.pushBackTight(i);
        }
        List<Integer> expected = new ArrayList<>();
        for (int i = 3; i >= 0; i--) {
            expected.add(i);
        }
        for (int i = 100; i < 105; i++) {
            expected.add(i);
        }
        assertThat(d.toList()).isEqualTo(expected);
    }
}
