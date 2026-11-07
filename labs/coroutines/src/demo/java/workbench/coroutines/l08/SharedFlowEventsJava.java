// Java equivalent of SharedFlowEvents.kt with Reactor sinks: a multicast sink with a small
// buffer refuses values when a slow subscriber can't keep up (FAIL_OVERFLOW), and a replay sink
// keeps the last N values for late subscribers.
package workbench.coroutines.l08;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import reactor.core.Disposable;
import reactor.core.publisher.Sinks;
import reactor.core.scheduler.Schedulers;

public class SharedFlowEventsJava {
    static void tryFive(String label, Sinks.Many<String> events) throws InterruptedException {
        List<String> received = new CopyOnWriteArrayList<>();
        Disposable auditor = events.asFlux()
            .publishOn(Schedulers.single(), 1)
            .subscribe(e -> { sleep(50); received.add(e); }); // the audit write takes 50 ms
        List<Sinks.EmitResult> results = new ArrayList<>();
        for (int i = 1; i <= 5; i++) results.add(events.tryEmitNext("e" + i));
        Thread.sleep(400);
        auditor.dispose();
        System.out.printf("%-34s tryEmitNext: %s  received: %s%n", label, results, received);
    }

    public static void main(String[] args) throws InterruptedException {
        tryFive("multicast, buffer of 2", Sinks.many().multicast().onBackpressureBuffer(2, false));
        tryFive("multicast, buffer of 64", Sinks.many().multicast().onBackpressureBuffer(64, false));

        Sinks.Many<String> replayed = Sinks.many().replay().limit(2);
        for (int i = 1; i <= 5; i++) replayed.tryEmitNext("e" + i); // no subscribers yet
        List<String> late = new ArrayList<>();
        replayed.asFlux().subscribe(late::add).dispose();
        System.out.println("a late subscriber to replay().limit(2) first gets: " + late);
    }

    static void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); } }
}
