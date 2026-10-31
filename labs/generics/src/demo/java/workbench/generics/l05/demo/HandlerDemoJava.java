package workbench.generics.l05.demo;

import java.util.function.Consumer;
import java.util.function.Function;

/**
 * Java twin of HandlerDemo.kt. Java's Consumer and Function are ordinary invariant interfaces,
 * so the flexibility has to be spelled at the use site: ? super for the input, ? extends for the output.
 */
public class HandlerDemoJava {
    public static void main(String[] args) {
        Consumer<PaymentEvent> auditAll = e -> System.out.println("audit " + e.getPaymentId());
        Function<PaymentEvent, String> describe = e -> "event " + e.getPaymentId();

        Consumer<? super CardAuthorized> onCard = auditAll;
        Function<? super CardAuthorized, ? extends Object> label = describe;
        onCard.accept(new CardAuthorized("pay_7", 4_200));
        System.out.println(label.apply(new CardAuthorized("pay_8", 10)));

        // Wrong moves. Uncomment ONE at a time, predict the error, then run.
        // Consumer<CardAuthorized> strict = auditAll;
        // Function<CardAuthorized, Object> strictFn = describe;
    }
}
