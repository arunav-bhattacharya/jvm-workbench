package workbench.performance.l04;

/**
 * Two counters for a settlement job. One thread settles card payments and only touches
 * {@code card}; another settles SEPA transfers and only touches {@code sepa}. Each counter
 * has one writer, so there is no race. But both fields sit on the same cache line, so the two
 * cores keep taking the line away from each other.
 *
 * <p>Your job: keep the fields named {@code card} and {@code sepa}, keep them {@code volatile long},
 * and lay the class out so they are at least 64 bytes apart. The test reads the real offsets with JOL.
 */
public final class SettlementCounters {
    private volatile long card;
    private volatile long sepa;

    /** Called only by the card-settlement thread. */
    public void addCard() { card++; }

    /** Called only by the SEPA-settlement thread. */
    public void addSepa() { sepa++; }

    public long card() { return card; }

    public long sepa() { return sepa; }
}
