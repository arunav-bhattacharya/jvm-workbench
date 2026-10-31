package workbench.executors.l03;

/** Thrown by {@link Bulkhead#call} when no permit became free within the bulkhead's maximum wait. */
public final class BulkheadFullException extends RuntimeException {
    public BulkheadFullException(String message) {
        super(message);
    }
}
