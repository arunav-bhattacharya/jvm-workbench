package workbench.patterns.l04;

/** The vendor SDK's checked exception. Given; don't edit. Your code must never let it escape. */
public class SdkException extends Exception {
    private final int status;

    public SdkException(int status, String message) {
        super(message);
        this.status = status;
    }

    public int status() { return status; }
}
