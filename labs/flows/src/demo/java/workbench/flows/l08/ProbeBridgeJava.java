package workbench.flows.l08;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import reactor.core.publisher.Flux;

// Java equivalent: the same probe library bridged with Reactor's Flux.create.
// Flux.create runs its lambda inside subscribe(), on the subscribing thread.
public class ProbeBridgeJava {

    static Flux<ProbeEvent> events(DemoProbe probe) {
        return Flux.create(sink -> {
            ProbeRegistration registration = probe.register(new ProbeEventListener() {
                @Override public void onEvent(ProbeEvent event) { sink.next(event); }
                @Override public void onError(Throwable error) { sink.error(error); }
                @Override public void onClosed() { sink.complete(); }
            });
            sink.onDispose(registration::unregister);   // on cancel, complete and error
        });
    }

    static Flux<ProbeEvent> eventsWithoutOnDispose(DemoProbe probe) {
        return Flux.create(sink -> probe.register(new ProbeEventListener() {
            @Override public void onEvent(ProbeEvent event) { sink.next(event); }
            @Override public void onError(Throwable error) { sink.error(error); }
            @Override public void onClosed() { sink.complete(); }
        }));
    }

    public static void main(String[] args) {
        System.out.println("== 0. fire right after subscribe: is the listener there yet?");
        DemoProbe probe0 = new DemoProbe();
        var d0 = events(probe0).subscribe(e -> System.out.println("  got " + e));
        probe0.fire(new ProbeEvent(0, 61));
        d0.dispose();

        System.out.println("== 1. Flux.create without onDispose: no error, and the listener stays");
        DemoProbe probe1 = new DemoProbe();
        eventsWithoutOnDispose(probe1).take(1).subscribe();
        probe1.fire(new ProbeEvent(1, 62));
        System.out.println("  after take(1) finished: listeners=" + probe1.getListeners().size());

        System.out.println("== 2. take(2) cancels, and onDispose unregisters");
        DemoProbe probe = new DemoProbe();
        List<ProbeEvent> two = new ArrayList<>();
        events(probe).take(2).subscribe(two::add);
        probe.fire(new ProbeEvent(1, 62)); probe.fire(new ProbeEvent(2, 63)); probe.fire(new ProbeEvent(3, 64));
        System.out.println("  got " + two);

        System.out.println("== 3. the probe reports an error: sink.error fails the Flux");
        DemoProbe probe3 = new DemoProbe();
        events(probe3).subscribe(e -> System.out.println("  got " + e),
                e -> System.out.println("  subscriber got onError " + e.getClass().getSimpleName() + ": " + e.getMessage()));
        probe3.fire(new ProbeEvent(4, 65));
        probe3.fail(new IOException("probe connection lost"));

        System.out.println("== 4. the probe says it is done: sink.complete completes the Flux");
        DemoProbe probe4 = new DemoProbe();
        List<ProbeEvent> all = new ArrayList<>();
        events(probe4).subscribe(all::add, e -> {}, () -> System.out.println("  completed with " + all));
        probe4.fire(new ProbeEvent(5, 66));
        probe4.close();
    }
}
