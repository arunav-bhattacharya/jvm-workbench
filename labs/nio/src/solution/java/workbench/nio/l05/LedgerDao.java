package workbench.nio.l05;

/** Stands in for a JDBC query against the ledger: it blocks the calling thread for 300 ms. */
public final class LedgerDao {
    public static final long QUERY_MILLIS = 300;

    private LedgerDao() { }

    /** The balance of {@code account} in cents. Blocks like a real JDBC call. */
    public static long balanceCents(String account) throws InterruptedException {
        Thread.sleep(QUERY_MILLIS);
        return 12_500;
    }
}
