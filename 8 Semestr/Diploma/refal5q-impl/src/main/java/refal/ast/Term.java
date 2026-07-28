package refal.ast;

// Базовый интерфейс терма Рефала-5. Подтипы: Sym, Num, Str, Var, Br, Call.
public sealed interface Term
        permits Sym, Num, Str, Var, Br, Call {
}
