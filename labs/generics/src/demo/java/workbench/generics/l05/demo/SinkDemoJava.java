package workbench.generics.l05.demo;

import java.util.List;

/**
 * Java twin of SinkDemo.kt. Java has no `in` on a declaration, so Sink<T> stays invariant and the
 * method that wants "a sink for card authorizations, or for anything more general" says ? super.
 */
public class SinkDemoJava {

    interface Sink<T> {
        void accept(T item);
    }

    static final Sink<PaymentEvent> AUDIT = e -> System.out.println("audit: " + e.getPaymentId());

    // ? super CardAuthorized: "a Sink of CardAuthorized or of some supertype"
    static void forwardAuthorizations(List<CardAuthorized> events, Sink<? super CardAuthorized> to) {
        for (CardAuthorized e : events) to.accept(e);
    }

    public static void main(String[] args) {
        forwardAuthorizations(List.of(new CardAuthorized("pay_1", 1_200), new CardAuthorized("pay_2", 350)), AUDIT);

        Sink<? super CardAuthorized> cardSink = AUDIT;   // the Java spelling of Kotlin's Sink<CardAuthorized>
        cardSink.accept(new CardAuthorized("pay_3", 99));

        // Wrong move. Uncomment, predict the error, then run.
        // Sink<CardAuthorized> strict = AUDIT;
    }
}
