package workbench.reactive.l06;

/**
 * The bakery's old stock book, reached through a blocking database driver: every call holds the
 * calling thread until the database answers, like a worker waiting on the phone.
 */
public interface StockBook {
    /** How many loaves the shop has left, for example {@code loavesLeft("shop-7")}. */
    int loavesLeft(String shop);
}
