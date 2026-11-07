package workbench.performance.l04;

// HotSpot lays out superclass fields before subclass fields, so a chain of classes puts the
// padding exactly where we want it. Fields of one class may be reordered; the chain may not.
abstract class CardCounter {
    volatile long card;
}

abstract class PadAfterCard extends CardCounter {
    long p1, p2, p3, p4, p5, p6, p7, p8;          // 64 bytes between card and sepa
}

abstract class SepaCounter extends PadAfterCard {
    volatile long sepa;
}

abstract class PadAfterSepa extends SepaCounter {
    long q1, q2, q3, q4, q5, q6, q7, q8;          // and 64 bytes after sepa, away from the next object
}

public final class SettlementCounters extends PadAfterSepa {
    public void addCard() { card++; }             // one writer per field: ++ on a volatile is safe here

    public void addSepa() { sepa++; }

    public long card() { return card; }

    public long sepa() { return sepa; }
}
