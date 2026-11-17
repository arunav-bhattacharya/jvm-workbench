package workbench.nio.l05;

/** Stands in for a database query against the price book: it blocks the calling thread for 300 ms. */
public final class PriceBook {
    public static final long LOOKUP_MILLIS = 300;

    private PriceBook() { }

    /** The postage for {@code parcel} in cents. Blocks like a real database call. */
    public static long postageCents(String parcel) throws InterruptedException {
        Thread.sleep(LOOKUP_MILLIS);
        return 1_250;
    }
}
