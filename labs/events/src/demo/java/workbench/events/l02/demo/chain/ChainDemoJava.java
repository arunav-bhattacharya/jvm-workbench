package workbench.events.l02.demo.chain;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class ChainDemoJava {
    sealed interface ParcelEvent permits ParcelCollected { String parcelId(); }
    record ParcelCollected(String parcelId, long grams) implements ParcelEvent {}

    @FunctionalInterface interface Next { int proceed(ParcelEvent event); }
    @FunctionalInterface interface Middleware { int intercept(ParcelEvent event, Next next); }

    @FunctionalInterface interface Handler {
        void handle(ParcelEvent event);

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
            System.out.println(name + " > " + event.parcelId());
            int called = next.proceed(event);
            System.out.println(name + " < " + event.parcelId() + ": " + called + " handler(s)");
            return called;
        };
    }

    static Middleware dropDuplicates() {
        Set<ParcelEvent> seen = new HashSet<>();
        return (event, next) -> seen.add(event) ? next.proceed(event) : 0;
    }

    public static void main(String[] args) {
        Handler load = ((Handler) e -> System.out.println("    load board adds " + e.parcelId())).timed("load");
        Next pipeline = chain(
                List.of(logging("outer"), dropDuplicates(), logging("inner")),    // Step 2: swap the first two
                e -> { load.handle(e); return 1; });
        ParcelCollected scan = new ParcelCollected("PP-7781", 2_500);
        pipeline.proceed(scan);
        System.out.println("-- the same scan again (the scanner sent it twice)");
        pipeline.proceed(new ParcelCollected("PP-7781", 2_500));
    }
}
