package workbench.generics.l06.demo;

import java.util.ArrayList;
import java.util.List;

/**
 * Java twin of ChooseDemo.kt. Java has only use-site variance, so every class is like Ledger:
 * invariant, with ? extends or ? super written by each method that only reads or only writes.
 */
public class ChooseDemoJava {

    static final class Ledger<T> {
        private final List<T> entries = new ArrayList<>();
        void record(T entry) { entries.add(entry); }
        T latest() { return entries.get(entries.size() - 1); }
    }

    // only reads: ? extends
    static String latestId(Ledger<? extends PaymentEvent> ledger) { return ledger.latest().getPaymentId(); }

    // only writes cards: ? super
    static void recordCard(Ledger<? super CardAuthorized> ledger, String id, long cents) {
        ledger.record(new CardAuthorized(id, cents));
    }

    public static void main(String[] args) {
        Ledger<CardAuthorized> cards = new Ledger<>();
        Ledger<PaymentEvent> everything = new Ledger<>();
        everything.record(new RefundIssued("pay_1", 500));

        recordCard(cards, "pay_2", 1_200);
        recordCard(everything, "pay_3", 350);
        System.out.println(latestId(cards) + " " + latestId(everything));

        // Wrong move: the class is invariant, so the plain type still doesn't fit.
        // Ledger<PaymentEvent> strict = cards;
    }
}
