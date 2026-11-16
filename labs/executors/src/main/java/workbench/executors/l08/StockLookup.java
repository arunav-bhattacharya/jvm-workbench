package workbench.executors.l08;

/** Asks the slow stock service how many of a product are left. Blocking: it calls a web service. */
public interface StockLookup {
    int level(String product);
}
