package refal.deque;

import java.util.Iterator;
import java.util.NoSuchElementException;

// Двусторонняя очередь на циклическом массиве фиксированной длины CAPACITY.
public final class ShallowDeque<T> implements Expr<T> {

    public static final int CAPACITY = 9;

    // Минимальная заполненность после расщепления.
    public static final int MIN_FILL = (CAPACITY + 1) / 2;

    private static final ShallowDeque<Object> EMPTY =
            new ShallowDeque<>(new Object[CAPACITY], 0, 0);

    private final Object[] buf;
    private final int head;
    private final int sz;

    private ShallowDeque(Object[] buf, int head, int sz) {
        this.buf = buf;
        this.head = head;
        this.sz = sz;
    }

    @SuppressWarnings("unchecked")
    public static <T> ShallowDeque<T> empty() {
        return (ShallowDeque<T>) EMPTY;
    }

    @Override
    public boolean isEmpty() {
        return sz == 0;
    }

    @Override
    public int size() {
        return sz;
    }

    public boolean isFull() {
        return sz == CAPACITY;
    }

    private int idx(int i) {
        return Math.floorMod(head + i, CAPACITY);
    }

    // Получить элемент по индексу 0..size-1.
    @SuppressWarnings("unchecked")
    public T get(int i) {
        if (i < 0 || i >= sz) {
            throw new IndexOutOfBoundsException("ShallowDeque.get(" + i + "), size=" + sz);
        }
        return (T) buf[idx(i)];
    }

    @Override
    public Expr<T> pushFront(T x) {
        if (isFull()) {
            var split = DeepDeque.splitForPushFront(this, x);
            return DeepDeque.mkDeep(
                    split.head(), Expr.empty(), split.tail(), CAPACITY + 1);
        }
        return pushFrontTight(x);
    }

    @Override
    public Expr<T> pushBack(T x) {
        if (isFull()) {
            var split = DeepDeque.splitForPushBack(this, x);
            return DeepDeque.mkDeep(
                    split.head(), Expr.empty(), split.tail(), CAPACITY + 1);
        }
        return pushBackTight(x);
    }

    // Версия pushFront, гарантированно возвращающая ShallowDeque (не DeepDeque).
    ShallowDeque<T> pushFrontTight(T x) {
        if (isFull()) {
            throw new IllegalStateException(
                    "ShallowDeque overflow on pushFrontTight");
        }
        Object[] nb = buf.clone();
        int newHead = Math.floorMod(head - 1, CAPACITY);
        nb[newHead] = x;
        return new ShallowDeque<>(nb, newHead, sz + 1);
    }

    /** Аналог pushFrontTight для конца буфера. */
    ShallowDeque<T> pushBackTight(T x) {
        if (isFull()) {
            throw new IllegalStateException(
                    "ShallowDeque overflow on pushBackTight");
        }
        Object[] nb = buf.clone();
        nb[idx(sz)] = x;
        return new ShallowDeque<>(nb, head, sz + 1);
    }

    @Override
    @SuppressWarnings("unchecked")
    public PeekResult<T> separateFront() {
        if (sz == 0) {
            throw new IllegalStateException("separateFront from empty deque");
        }
        T x = (T) buf[head];
        Object[] nb = buf.clone();
        nb[head] = null;
        int newHead = Math.floorMod(head + 1, CAPACITY);
        return new PeekResult<>(x, new ShallowDeque<>(nb, newHead, sz - 1));
    }

    @Override
    @SuppressWarnings("unchecked")
    public PeekResult<T> separateBack() {
        if (sz == 0) {
            throw new IllegalStateException("separateBack from empty deque");
        }
        int last = idx(sz - 1);
        T x = (T) buf[last];
        Object[] nb = buf.clone();
        nb[last] = null;
        return new PeekResult<>(x, new ShallowDeque<>(nb, head, sz - 1));
    }

    @Override
    public Iterator<T> iterator() {
        return new Iterator<>() {
            private int i;

            @Override
            public boolean hasNext() {
                return i < sz;
            }

            @Override
            @SuppressWarnings("unchecked")
            public T next() {
                if (i >= sz) {
                    throw new NoSuchElementException();
                }
                return (T) buf[idx(i++)];
            }
        };
    }

    // Создать буфер из среза массива.
    static <T> ShallowDeque<T> ofArray(Object[] elements, int from, int len) {
        if (len < 0 || len > CAPACITY) {
            throw new IllegalArgumentException(
                    "ofArray: bad length " + len + " (CAPACITY=" + CAPACITY + ")");
        }
        Object[] nb = new Object[CAPACITY];
        for (int i = 0; i < len; i++) {
            nb[i] = elements[from + i];
        }
        return new ShallowDeque<>(nb, 0, len);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof ShallowDeque<?> that)) {
            return false;
        }
        if (sz != that.sz) {
            return false;
        }
        for (int i = 0; i < sz; i++) {
            Object a = buf[idx(i)];
            Object b = that.buf[that.idx(i)];
            if (a == null ? b != null : !a.equals(b)) {
                return false;
            }
        }
        return true;
    }

    @Override
    public int hashCode() {
        int h = 1;
        for (int i = 0; i < sz; i++) {
            Object x = buf[idx(i)];
            h = 31 * h + (x == null ? 0 : x.hashCode());
        }
        return h;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder("Shallow[");
        for (int i = 0; i < sz; i++) {
            if (i > 0) {
                sb.append(", ");
            }
            sb.append(buf[idx(i)]);
        }
        sb.append(']');
        return sb.toString();
    }
}
