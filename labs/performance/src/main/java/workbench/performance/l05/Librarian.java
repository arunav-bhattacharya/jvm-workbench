package workbench.performance.l05;

/**
 * Fetches documents from the store for the report service. It works, but nobody can see how long
 * the store takes, or which shelves are missing documents.
 *
 * <p>TODO: record one {@link LookupEvent} per call. Start timing just before the store call,
 * stop just after it, fill in the fields, and commit. Keep the return value as it is.
 */
public final class Librarian {
    private final DocumentStore store;

    public Librarian(DocumentStore store) {
        this.store = store;
    }

    /** The document's text, or null when the shelf doesn't have it. */
    public String lookup(String shelf, String title) {
        return store.fetch(shelf, title);
    }
}
