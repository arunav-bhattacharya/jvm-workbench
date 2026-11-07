package workbench.ledger.l02;

/**
 * The durable log the ledger writes before it changes a balance (a write-ahead log). A real one
 * appends to a file or a table and waits for the disk, which takes milliseconds. It may block, and
 * it may be interrupted, in which case the transfer is not applied.
 */
@FunctionalInterface
public interface Journal {
    void append(Transfer t) throws InterruptedException;

    /** A journal that writes nothing, for tests and demos. */
    Journal NONE = t -> { };
}
