package workbench.patterns.l04;

/** Our port: the only way the shop's code talks to any warehouse. Given; don't edit. */
public interface Warehouse {

    StockResult reserve(String product, long grams);

    /** What a reservation can come back as, in our words, not the warehouse program's. */
    sealed interface StockResult {
        record Reserved(String holdId) implements StockResult {}
        record Refused(String reason) implements StockResult {}
        record Unavailable(String detail) implements StockResult {}
    }
}
