package refal.deque;

import java.util.Iterator;
import java.util.NoSuchElementException;

import static refal.deque.ShallowDeque.CAPACITY;
import static refal.deque.ShallowDeque.MIN_FILL;

public final class DeepDeque<T> implements Expr<T> {

    private final ShallowDeque<T> front;
    private final Expr<ShallowDeque<T>> mid;
    private final ShallowDeque<T> back;
    private final int sz;

    private DeepDeque(
            ShallowDeque<T> front,
            Expr<ShallowDeque<T>> mid,
            ShallowDeque<T> back,
            int sz) {
        this.front = front;
        this.mid = mid;
        this.back = back;
        this.sz = sz;
    }

    // Умный конструктор: если суммарный размер помещается в ShallowDeque, делаем его.
    static <T> Expr<T> mkDeep(
            ShallowDeque<T> front,
            Expr<ShallowDeque<T>> mid,
            ShallowDeque<T> back,
            int total) {
        if (total <= CAPACITY) {
            ShallowDeque<T> flat = ShallowDeque.empty();
            for (T x : iterableOf(front)) {
                flat = flat.pushBackTight(x);
            }
            for (ShallowDeque<T> bucket : iterableOf(mid)) {
                for (T x : iterableOf(bucket)) {
                    flat = flat.pushBackTight(x);
                }
            }
            for (T x : iterableOf(back)) {
                flat = flat.pushBackTight(x);
            }
            return flat;
        }
        return new DeepDeque<>(front, mid, back, total);
    }

    private static <X> Iterable<X> iterableOf(Expr<X> e) {
        return e::iterator;
    }

    @Override
    public boolean isEmpty() {
        return sz == 0;
    }

    @Override
    public int size() {
        return sz;
    }

    ShallowDeque<T> front() {
        return front;
    }

    Expr<ShallowDeque<T>> mid() {
        return mid;
    }

    ShallowDeque<T> back() {
        return back;
    }

    @Override
    public Expr<T> pushFront(T x) {
        if (!front.isFull()) {
            return new DeepDeque<>(front.pushFrontTight(x), mid, back, sz + 1);
        }
        // Разбить [x, front[0..C-1]] в [first MIN_FILL] и [tail].
        var split = splitForPushFront(front, x);
        return mkDeep(split.head(), mid.pushFront(split.tail()), back, sz + 1);
    }

    @Override
    public Expr<T> pushBack(T x) {
        if (!back.isFull()) {
            return new DeepDeque<>(front, mid, back.pushBackTight(x), sz + 1);
        }
        // Разбить [back[0..C-1], x] в [head] и [last MIN_FILL].
        var split = splitForPushBack(back, x);
        return mkDeep(front, mid.pushBack(split.head()), split.tail(), sz + 1);
    }

    @Override
    public PeekResult<T> separateFront() {
        if (sz == 0) {
            throw new IllegalStateException("separateFront from empty DeepDeque");
        }
        DeepDeque<T> norm = normalizeForFront();
        var pr = norm.front.separateFront();
        @SuppressWarnings("unchecked")
        ShallowDeque<T> restFront = (ShallowDeque<T>) pr.rest();
        return new PeekResult<>(pr.term(),
                mkDeep(restFront, norm.mid, norm.back, sz - 1));
    }

    @Override
    public PeekResult<T> separateBack() {
        if (sz == 0) {
            throw new IllegalStateException("separateBack from empty DeepDeque");
        }
        DeepDeque<T> norm = normalizeForBack();
        var pr = norm.back.separateBack();
        @SuppressWarnings("unchecked")
        ShallowDeque<T> restBack = (ShallowDeque<T>) pr.rest();
        return new PeekResult<>(pr.term(),
                mkDeep(norm.front, norm.mid, restBack, sz - 1));
    }

    private DeepDeque<T> normalizeForFront() {
        if (!front.isEmpty()) {
            return this;
        }
        if (!mid.isEmpty()) {
            var pr = mid.separateFront();
            return new DeepDeque<>(pr.term(), pr.rest(), back, sz);
        }
        // mid пуст, front пуст — поднимаем back наверх как новый front.
        if (!back.isEmpty()) {
            return new DeepDeque<>(back, ShallowDeque.empty(), ShallowDeque.empty(), sz);
        }
        throw new IllegalStateException("DeepDeque with size>0 has no elements");
    }

    private DeepDeque<T> normalizeForBack() {
        if (!back.isEmpty()) {
            return this;
        }
        if (!mid.isEmpty()) {
            var pr = mid.separateBack();
            return new DeepDeque<>(front, pr.rest(), pr.term(), sz);
        }
        if (!front.isEmpty()) {
            return new DeepDeque<>(ShallowDeque.empty(), ShallowDeque.empty(), front, sz);
        }
        throw new IllegalStateException("DeepDeque with size>0 has no elements");
    }

    @Override
    public Iterator<T> iterator() {
        return new Iterator<>() {
            private final Iterator<T> frontIt = front.iterator();
            private final Iterator<ShallowDeque<T>> midIt = mid.iterator();
            private final Iterator<T> backIt = back.iterator();
            private Iterator<T> midBucketIt = java.util.Collections.emptyIterator();

            @Override
            public boolean hasNext() {
                if (frontIt.hasNext()) {
                    return true;
                }
                if (midBucketIt.hasNext()) {
                    return true;
                }
                while (midIt.hasNext() && !midBucketIt.hasNext()) {
                    midBucketIt = midIt.next().iterator();
                }
                if (midBucketIt.hasNext()) {
                    return true;
                }
                return backIt.hasNext();
            }

            @Override
            public T next() {
                if (!hasNext()) {
                    throw new NoSuchElementException();
                }
                if (frontIt.hasNext()) {
                    return frontIt.next();
                }
                if (midBucketIt.hasNext()) {
                    return midBucketIt.next();
                }
                return backIt.next();
            }
        };
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof Expr<?> that)) {
            return false;
        }
        if (this.size() != that.size()) {
            return false;
        }
        var i1 = this.iterator();
        var i2 = that.iterator();
        while (i1.hasNext()) {
            Object a = i1.next();
            Object b = i2.next();
            if (a == null ? b != null : !a.equals(b)) {
                return false;
            }
        }
        return true;
    }

    @Override
    public int hashCode() {
        int h = 1;
        for (Iterator<T> it = iterator(); it.hasNext(); ) {
            T x = it.next();
            h = 31 * h + (x == null ? 0 : x.hashCode());
        }
        return h;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder("Deep[");
        var it = iterator();
        boolean first = true;
        while (it.hasNext()) {
            if (!first) {
                sb.append(", ");
            }
            sb.append(it.next());
            first = false;
        }
        sb.append(']');
        return sb.toString();
    }

    record SplitPair<T>(ShallowDeque<T> head, ShallowDeque<T> tail) {
    }

    // Расщепить полный front-буфер с новым элементом слева на два подбуфера.
    static <T> SplitPair<T> splitForPushFront(ShallowDeque<T> full, T x) {
        if (!full.isFull()) {
            throw new IllegalArgumentException("splitForPushFront expects full buffer");
        }
        Object[] tmp = new Object[CAPACITY + 1];
        tmp[0] = x;
        for (int i = 0; i < CAPACITY; i++) {
            tmp[i + 1] = full.get(i);
        }
        ShallowDeque<T> head = ShallowDeque.ofArray(tmp, 0, MIN_FILL);
        ShallowDeque<T> tail = ShallowDeque.ofArray(tmp, MIN_FILL, CAPACITY + 1 - MIN_FILL);
        return new SplitPair<>(head, tail);
    }

    // Расщепить полный back-буфер с новым элементом справа на два подбуфера.
    static <T> SplitPair<T> splitForPushBack(ShallowDeque<T> full, T x) {
        if (!full.isFull()) {
            throw new IllegalArgumentException("splitForPushBack expects full buffer");
        }
        Object[] tmp = new Object[CAPACITY + 1];
        for (int i = 0; i < CAPACITY; i++) {
            tmp[i] = full.get(i);
        }
        tmp[CAPACITY] = x;
        int total = CAPACITY + 1;
        ShallowDeque<T> head = ShallowDeque.ofArray(tmp, 0, total - MIN_FILL);
        ShallowDeque<T> tail = ShallowDeque.ofArray(tmp, total - MIN_FILL, MIN_FILL);
        return new SplitPair<>(head, tail);
    }
}
