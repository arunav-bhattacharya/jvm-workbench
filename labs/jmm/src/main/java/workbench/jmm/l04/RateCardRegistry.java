package workbench.jmm.l04;

/**
 * Holds the current rate card. A loader thread calls {@link #publish}; request threads call
 * {@link #current()} or wait in {@link #awaitFirst()}.
 *
 * <p>The bug: the card is published through a plain field. A waiting reader may never see it,
 * and final fields in RateCard don't change that. Publish it safely.
 */
public class RateCardRegistry {
    private RateCard current;

    public void publish(RateCard card) {
        current = card;
    }

    public RateCard current() {
        return current;
    }

    /** Spins until a card has been published, then returns it. */
    public RateCard awaitFirst() {
        RateCard c;
        while ((c = current) == null) {
            // wait for the loader
        }
        return c;
    }
}
