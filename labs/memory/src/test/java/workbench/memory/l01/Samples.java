package workbench.memory.l01;

/** Classes the tests measure. Predict each size before you run the tests. */
final class Samples {
    private Samples() {}

    /** The same fields as the JOL printout in the lesson. */
    static class Payment {
        boolean captured;
        long amountMinor;
        byte status;
        String currency;
        int attempts;
        Object metadata;
    }

    /** A subclass: its object holds Payment's fields too. */
    static class CardPayment extends Payment {
        String cardToken;
        short networkCode;
    }

    static class LedgerEntry {
        long amountMinor;
        long balanceAfterMinor;
        String accountId;
        char sign;
    }

    /** Static fields live with the class, so they add nothing to each object. */
    static class FeeRule {
        static final long MAX_FEE_MINOR = 5_000;
        static int rulesLoaded;
        int basisPoints;
    }

    record Money(long amountMinor, String currency) {}
}
