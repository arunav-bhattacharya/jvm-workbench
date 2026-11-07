package workbench.ledger.l01;

/**
 * One request to move {@code cents} from account {@code from} to account {@code to}.
 *
 * <p>A transfer is built on one thread (an importer, an HTTP handler) and read on others (the
 * ledger, the journal, the logs). It must never change after it is built, and a record gives you
 * that: final fields, no setters.
 *
 * <p>TODO: make every Transfer that exists a valid one. Add a compact constructor that throws
 * {@link NullPointerException} when {@code id}, {@code from} or {@code to} is null, and
 * {@link IllegalArgumentException} when {@code cents} is zero or negative, or when
 * {@code from} equals {@code to}. Then the ledger never has to handle a bad transfer.
 */
public record Transfer(String id, String from, String to, long cents) {
}
