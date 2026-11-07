package workbench.memory.l07;

/** A client reused an idempotency key with a different request body. */
public class IdempotencyConflictException extends RuntimeException {
    public IdempotencyConflictException(String idempotencyKey) {
        super("idempotency key reused with a different body: " + idempotencyKey);
    }
}
