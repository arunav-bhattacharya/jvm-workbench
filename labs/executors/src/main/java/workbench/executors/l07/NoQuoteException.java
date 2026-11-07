package workbench.executors.l07;

/** Thrown when no provider answered in time. */
public class NoQuoteException extends RuntimeException {
    public NoQuoteException(String pair) {
        super("no provider quoted " + pair + " in time");
    }
}
