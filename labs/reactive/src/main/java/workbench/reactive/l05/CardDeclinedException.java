package workbench.reactive.l05;

/** The issuer said no. Asking again gives the same answer, so never retry this. */
public class CardDeclinedException extends RuntimeException {
    public CardDeclinedException(String message) {
        super(message);
    }
}
