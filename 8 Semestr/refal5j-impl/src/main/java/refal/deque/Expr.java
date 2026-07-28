package refal.deque;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public sealed interface Expr<T> extends Iterable<T> permits ShallowDeque, DeepDeque {

    /** Истина, если выражение пусто. */
    boolean isEmpty();

    /** Размер выражения (количество термов на верхнем уровне). */
    int size();

    /** Отделить первый терм.*/
    PeekResult<T> separateFront();

    /** Отделить последний терм. */
    PeekResult<T> separateBack();

    /** Добавить терм слева.*/
    Expr<T> pushFront(T x);

    /** Добавить терм справа. */
    Expr<T> pushBack(T x);

    /** Итерация по элементам в порядке front → back. */
    Iterator<T> iterator();

    /** Конкатенация двух выражений. */
    static <T> Expr<T> concat(Expr<T> a, Expr<T> b) {
        return ExprOps.concat(a, b);
    }

    /** Пустое выражение. */
    static <T> Expr<T> empty() {
        return ShallowDeque.empty();
    }

    /** Выражение из одного элемента. */
    static <T> Expr<T> singleton(T x) {
        return ShallowDeque.<T>empty().pushBack(x);
    }

    /** Построить выражение из обычного списка.*/
    static <T> Expr<T> fromList(List<? extends T> xs) {
        Expr<T> d = empty();
        for (T x : xs) {
            d = d.pushBack(x);
        }
        return d;
    }

    // Скопировать содержимое в обычный список.
    default List<T> toList() {
        var out = new ArrayList<T>(size());
        for (Iterator<T> it = iterator(); it.hasNext(); ) {
            out.add(it.next());
        }
        return out;
    }
}
