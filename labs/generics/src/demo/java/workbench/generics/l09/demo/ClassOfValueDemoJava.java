package workbench.generics.l09.demo;

import java.util.List;

/** Java twin of ClassOfValueDemo.kt. getClass() is declared to return Class<? extends |X|>. */
public class ClassOfValueDemoJava {
    public static void main(String[] args) {
        List<PaymentEvent> events = List.of(new CardAuthorized("pay_1", 1_200), new RefundIssued("pay_2", 500));
        for (PaymentEvent event : events) {
            Class<? extends PaymentEvent> c = event.getClass();   // the class of SOME PaymentEvent
            System.out.println(event.getPaymentId() + ": " + c.getSimpleName() + ", is a card: " + (c == CardAuthorized.class));
        }

        Class<CardAuthorized> exact = CardAuthorized.class;       // a class literal is exact
        String note = null;                                        // a value that turns out to be null
        try {
            System.out.println(note.getClass());
        } catch (NullPointerException e) {
            System.out.println("exact = " + exact.getSimpleName() + ", getClass() on null: NullPointerException");
        }

        // Wrong move. Uncomment, predict the error, then run.
        // Class<PaymentEvent> strict = events.get(0).getClass();
    }
}
