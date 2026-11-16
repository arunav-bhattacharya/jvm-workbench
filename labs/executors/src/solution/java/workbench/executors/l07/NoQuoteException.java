package workbench.executors.l07;

/** Thrown when no supplier answered in time. */
public class NoQuoteException extends RuntimeException {
    public NoQuoteException(String item) {
        super("no supplier quoted a price for " + item + " in time");
    }
}
