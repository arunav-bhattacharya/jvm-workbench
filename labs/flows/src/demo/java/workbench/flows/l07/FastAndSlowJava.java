package workbench.flows.l07;

import java.util.ArrayList;
import java.util.List;
import org.reactivestreams.Subscription;
import reactor.core.publisher.BaseSubscriber;
import reactor.core.publisher.Sinks;

// Java equivalent: Reactor multicast sinks with one fast subscriber and one slow one.
// The slow audit writer asks for one transition and then nothing more until the end,
// as if stuck on its first row. Everything runs on the main thread, so no timing is involved.
public class FastAndSlowJava {

    static final class SlowAudit extends BaseSubscriber<Integer> {
        final List<Integer> got = new ArrayList<>();
        @Override protected void hookOnSubscribe(Subscription s) { request(1); }
        @Override protected void hookOnNext(Integer v) { got.add(v); }
    }

    static void run(String label, Sinks.Many<Integer> bus) {
        List<Integer> notifier = new ArrayList<>();
        bus.asFlux().subscribe(notifier::add);       // unbounded demand
        SlowAudit audit = new SlowAudit();
        bus.asFlux().subscribe(audit);               // demand of 1
        List<String> results = new ArrayList<>();
        for (int t = 1; t <= 6; t++) results.add(t + "=" + bus.tryEmitNext(t));
        audit.request(Long.MAX_VALUE);               // the audit writer catches up at the end
        System.out.println(label);
        System.out.println("  tryEmitNext: " + results);
        System.out.println("  notifier got " + notifier);
        System.out.println("  audit got    " + audit.got);
    }

    public static void main(String[] args) {
        run("multicast().directAllOrNothing()", Sinks.many().multicast().directAllOrNothing());
        run("multicast().onBackpressureBuffer(2, false)", Sinks.many().multicast().onBackpressureBuffer(2, false));
        run("multicast().directBestEffort()", Sinks.many().multicast().directBestEffort());
    }
}
