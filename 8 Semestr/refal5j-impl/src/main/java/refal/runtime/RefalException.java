package refal.runtime;

// Ошибка времени выполнения: нет правила, лимит шагов, неверный аргумент и т.д.
public class RefalException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    public RefalException(String message) {
        super(message);
    }
}
