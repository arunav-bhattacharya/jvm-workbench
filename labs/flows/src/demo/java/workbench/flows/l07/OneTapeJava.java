package workbench.flows.l07;

import java.util.ArrayList;
import java.util.List;
import org.reactivestreams.Subscription;
import reactor.core.publisher.BaseSubscriber;
import reactor.core.publisher.Sinks;

// Java equivalent: Reactor sinks are driven by demand. A subscriber says "I can take n"
// with request(n) BEFORE anything is emitted, so a sink can push straight into it.
public class OneTapeJava {

    static final class Waiting extends BaseSubscriber<Integer> {
        final List<Integer> got = new ArrayList<>();
        @Override protected void hookOnSubscribe(Subscription s) { request(1); }   // idle, ready for one
        @Override protected void hookOnNext(Integer v) { got.add(v); }
    }

    static void table(String label, Sinks.Many<Integer> sink, int subscribers) {
        Waiting first = null;
        for (int i = 0; i < subscribers; i++) {
            Waiting w = new Waiting();
            sink.asFlux().subscribe(w);
            if (first == null) first = w;
        }
        List<String> results = new ArrayList<>();
        for (int v = 1; v <= 6; v++) results.add(sink.tryEmitNext(v).toString());
        if (first != null) first.request(Long.MAX_VALUE);
        System.out.printf("%-36s subscribers=%d  %s  received: %s%n", label, subscribers, results,
                first == null ? "[]" : first.got);
    }

    public static void main(String[] args) {
        System.out.println("== tryEmitNext(1..6), each subscriber has requested 1");
        table("multicast().directAllOrNothing()", Sinks.many().multicast().directAllOrNothing(), 0);
        table("multicast().directAllOrNothing()", Sinks.many().multicast().directAllOrNothing(), 1);
        table("multicast().onBackpressureBuffer(2)", Sinks.many().multicast().onBackpressureBuffer(2, false), 1);
        table("replay().limit(2)", Sinks.many().replay().limit(2), 1);

        System.out.println("== a late subscriber to replay().limit(1)");
        Sinks.Many<Integer> bus = Sinks.many().replay().limit(1);
        Waiting s1 = new Waiting();
        bus.asFlux().subscribe(s1);
        for (int v = 1; v <= 5; v++) bus.tryEmitNext(v);  // S1 is still on its first item
        List<Integer> s2 = new ArrayList<>();
        bus.asFlux().subscribe(s2::add);
        s1.request(Long.MAX_VALUE);
        System.out.println("  S1 got " + s1.got + ", S2 (joined after 5) got " + s2);
    }
}
