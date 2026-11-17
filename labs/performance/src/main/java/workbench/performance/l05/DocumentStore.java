package workbench.performance.l05;

/**
 * Where the report service keeps its documents: another program, reached over the network.
 * Real ones take 100 ms or more to answer.
 */
@FunctionalInterface
public interface DocumentStore {
    /** The text of the document with this title on this shelf, or null if the shelf doesn't have it. */
    String fetch(String shelf, String title);
}
