package workbench.events.l02.demo.chain;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class ChainDemoJava {
    sealed interface PaymentEvent permits PaymentCaptured { String paymentId(); }
    record PaymentCaptured(String paymentId, long cents) implements PaymentEvent {}

    @FunctionalInterface interface Next { int proceed(PaymentEvent event); }
    @FunctionalInterface interface Middleware { int intercept(PaymentEvent event, Next next); }

    @FunctionalInterface interface Handler {
        void handle(PaymentEvent event);

        /** Decorator: the same Handler interface, plus timing. Virtual time keeps the output stable. */
        default Handler timed(String name) {
            return event -> {
                long start = tick();
                try { handle(event); } finally { System.out.println("    " + name + " took " + (tick() - start) / 1_000 + " us"); }
            };
        }
    }

    static long clock = 0;
    static long tick() { clock += 40_000; return clock; }     // every read moves the clock by 40 microseconds

    /** Chain of responsibility: each middleware passes the event on, or answers 0 itself. */
    static Next chain(List<Middleware> middleware, Next deliver) {
        Next next = deliver;
        for (int i = middleware.size() - 1; i >= 0; i--) {
            Middleware m = middleware.get(i);
            Next rest = next;
            next = e -> m.intercept(e, rest);
        }
        return next;
    }

    static Middleware logging(String name) {
        return (event, next) -> {
            System.out.println(name + " > " + event.paymentId());
            int called = next.proceed(event);
            System.out.println(name + " < " + event.paymentId() + ": " + called + " handler(s)");
            return called;
        };
    }

    static Middleware dropDuplicates() {
        Set<PaymentEvent> seen = new HashSet<>();
        return (event, next) -> seen.add(event) ? next.proceed(event) : 0;
    }

    public static void main(String[] args) {
        Handler ledger = ((Handler) e -> System.out.println("    ledger posts " + e.paymentId())).timed("ledger");
        Next pipeline = chain(
                List.of(logging("outer"), dropDuplicates(), logging("inner")),    // Step 2: swap the first two
                e -> { ledger.handle(e); return 1; });
        PaymentCaptured capture = new PaymentCaptured("pay_7781", 1_999);
        pipeline.proceed(capture);
        System.out.println("-- the same capture again (a Kafka redelivery)");
        pipeline.proceed(new PaymentCaptured("pay_7781", 1_999));
    }
}
