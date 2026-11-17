package workbench.reactive.l05;

/** The mill said no, for example because it has no rye flour this week. Asking again gives the same answer, so never retry this. */
public class OrderRefusedException extends RuntimeException {
    public OrderRefusedException(String message) {
        super(message);
    }
}
