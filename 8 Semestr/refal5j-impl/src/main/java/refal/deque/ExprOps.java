package refal.deque;

import static refal.deque.ShallowDeque.CAPACITY;

// Конкатенация двух Expr через слияние пограничных буферов.
// Четыре комбинации: Shallow+Shallow, Shallow+Deep, Deep+Shallow, Deep+Deep.
final class ExprOps {

    private ExprOps() {
    }

    static <T> Expr<T> concat(Expr<T> a, Expr<T> b) {
        if (a.isEmpty()) {
            return b;
        }
        if (b.isEmpty()) {
            return a;
        }
        if (a instanceof ShallowDeque<T> sa && b instanceof ShallowDeque<T> sb) {
            return concatSS(sa, sb);
        }
        if (a instanceof ShallowDeque<T> sa && b instanceof DeepDeque<T> db) {
            return concatSD(sa, db);
        }
        if (a instanceof DeepDeque<T> da && b instanceof ShallowDeque<T> sb) {
            return concatDS(da, sb);
        }
        // Обе стороны Deep.
        DeepDeque<T> da = (DeepDeque<T>) a;
        DeepDeque<T> db = (DeepDeque<T>) b;
        return concatDD(da, db);
    }

    private static <T> Expr<T> concatSS(ShallowDeque<T> a, ShallowDeque<T> b) {
        int total = a.size() + b.size();
        if (total <= CAPACITY) {
            ShallowDeque<T> r = a;
            for (T x : iter(b)) {
                r = r.pushBackTight(x);
            }
            return r;
        }
        // total > CAPACITY: один из буферов «полный или почти полный»;
        // делаем новый Deep с пустой mid.
        return DeepDeque.mkDeep(a, ShallowDeque.empty(), b, total);
    }

    private static <T> Expr<T> concatSD(ShallowDeque<T> a, DeepDeque<T> b) {
        ShallowDeque<T> bf = b.front();
        int total = b.size() + a.size();
        // Сливаем 'a' слева в b.front. Если итог влезает в один Shallow,
        // он становится новым front; иначе — расщепляем на два, второй идёт
        // в начало mid.
        int bfTotal = a.size() + bf.size();
        if (bfTotal <= CAPACITY) {
            ShallowDeque<T> mergedFront = ShallowDeque.empty();
            for (T x : iter(a)) {
                mergedFront = mergedFront.pushBackTight(x);
            }
            for (T x : iter(bf)) {
                mergedFront = mergedFront.pushBackTight(x);
            }
            return DeepDeque.mkDeep(mergedFront, b.mid(), b.back(), total);
        }
        // Иначе формируем плоский массив и делим примерно пополам.
        Object[] tmp = new Object[bfTotal];
        int i = 0;
        for (T x : iter(a)) {
            tmp[i++] = x;
        }
        for (T x : iter(bf)) {
            tmp[i++] = x;
        }
        int leftLen = bfTotal - CAPACITY;
        if (leftLen < ShallowDeque.MIN_FILL) {
            leftLen = ShallowDeque.MIN_FILL;
        }
        int rightLen = bfTotal - leftLen;
        ShallowDeque<T> head = ShallowDeque.ofArray(tmp, 0, leftLen);
        ShallowDeque<T> tail = ShallowDeque.ofArray(tmp, leftLen, rightLen);
        // head становится новым front; tail — первым бакетом mid.
        Expr<ShallowDeque<T>> newMid = b.mid().pushFront(tail);
        return DeepDeque.mkDeep(head, newMid, b.back(), total);
    }

    private static <T> Expr<T> concatDS(DeepDeque<T> a, ShallowDeque<T> b) {
        ShallowDeque<T> ab = a.back();
        int total = a.size() + b.size();
        int abTotal = ab.size() + b.size();
        if (abTotal <= CAPACITY) {
            ShallowDeque<T> mergedBack = ShallowDeque.empty();
            for (T x : iter(ab)) {
                mergedBack = mergedBack.pushBackTight(x);
            }
            for (T x : iter(b)) {
                mergedBack = mergedBack.pushBackTight(x);
            }
            return DeepDeque.mkDeep(a.front(), a.mid(), mergedBack, total);
        }
        Object[] tmp = new Object[abTotal];
        int i = 0;
        for (T x : iter(ab)) {
            tmp[i++] = x;
        }
        for (T x : iter(b)) {
            tmp[i++] = x;
        }
        int rightLen = abTotal - CAPACITY;
        if (rightLen < ShallowDeque.MIN_FILL) {
            rightLen = ShallowDeque.MIN_FILL;
        }
        int leftLen = abTotal - rightLen;
        ShallowDeque<T> head = ShallowDeque.ofArray(tmp, 0, leftLen);
        ShallowDeque<T> tail = ShallowDeque.ofArray(tmp, leftLen, rightLen);
        Expr<ShallowDeque<T>> newMid = a.mid().pushBack(head);
        return DeepDeque.mkDeep(a.front(), newMid, tail, total);
    }

    private static <T> Expr<T> concatDD(DeepDeque<T> a, DeepDeque<T> b) {
        int total = a.size() + b.size();
        ShallowDeque<T> ab = a.back();
        ShallowDeque<T> bf = b.front();
        int boundary = ab.size() + bf.size();

        Expr<ShallowDeque<T>> aMidPlus = a.mid();
        if (boundary == 0) {
            // оба пограничных пусты — ничего не добавляем.
        } else if (boundary <= CAPACITY) {
            ShallowDeque<T> merged = ShallowDeque.empty();
            for (T x : iter(ab)) {
                merged = merged.pushBackTight(x);
            }
            for (T x : iter(bf)) {
                merged = merged.pushBackTight(x);
            }
            aMidPlus = aMidPlus.pushBack(merged);
        } else {
            Object[] tmp = new Object[boundary];
            int i = 0;
            for (T x : iter(ab)) {
                tmp[i++] = x;
            }
            for (T x : iter(bf)) {
                tmp[i++] = x;
            }
            int rightLen = boundary - CAPACITY;
            if (rightLen < ShallowDeque.MIN_FILL) {
                rightLen = ShallowDeque.MIN_FILL;
            }
            int leftLen = boundary - rightLen;
            ShallowDeque<T> m1 = ShallowDeque.ofArray(tmp, 0, leftLen);
            ShallowDeque<T> m2 = ShallowDeque.ofArray(tmp, leftLen, rightLen);
            aMidPlus = aMidPlus.pushBack(m1).pushBack(m2);
        }

        // Рекурсивное склеивание middle-очередей буферов.
        Expr<ShallowDeque<T>> newMid = concat(aMidPlus, b.mid());
        return DeepDeque.mkDeep(a.front(), newMid, b.back(), total);
    }

    private static <X> Iterable<X> iter(Expr<X> e) {
        return e::iterator;
    }
}
