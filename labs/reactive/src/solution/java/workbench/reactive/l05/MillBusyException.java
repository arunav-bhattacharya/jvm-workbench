package workbench.reactive.l05;

/** The mill is overloaded or briefly down: a later attempt may succeed. */
public class MillBusyException extends RuntimeException {
    public MillBusyException(String message) {
        super(message);
    }
}
