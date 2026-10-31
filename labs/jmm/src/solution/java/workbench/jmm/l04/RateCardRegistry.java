package workbench.jmm.l04;

public class RateCardRegistry {
    // volatile: the write in publish() is a release, the read in current()/awaitFirst() an acquire.
    // That makes the reference visible, and everything written before publish() with it.
    private volatile RateCard current;

    public void publish(RateCard card) {
        current = card;
    }

    public RateCard current() {
        return current;
    }

    public RateCard awaitFirst() {
        RateCard c;
        while ((c = current) == null) {
            Thread.onSpinWait();
        }
        return c;
    }
}
