package workbench.patterns.l04;

/** The old warehouse program's checked exception. Given; don't edit. Your code must never let it escape. */
public class WarehouseException extends Exception {
    private final int status;

    public WarehouseException(int status, String message) {
        super(message);
        this.status = status;
    }

    public int status() { return status; }
}
