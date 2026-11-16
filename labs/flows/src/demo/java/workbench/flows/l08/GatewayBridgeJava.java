package workbench.flows.l08;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import reactor.core.publisher.Flux;

// Java equivalent: the same gateway SDK bridged with Reactor's Flux.create.
// Flux.create runs its lambda inside subscribe(), on the subscribing thread.
public class GatewayBridgeJava {

    static Flux<PayEvent> events(DemoGateway gw) {
        return Flux.create(sink -> {
            PayRegistration registration = gw.register(new PayListener() {
                @Override public void onEvent(PayEvent event) { sink.next(event); }
                @Override public void onError(Throwable error) { sink.error(error); }
                @Override public void onClosed() { sink.complete(); }
            });
            sink.onDispose(registration::unregister);   // on cancel, complete and error
        });
    }

    static Flux<PayEvent> eventsWithoutOnDispose(DemoGateway gw) {
        return Flux.create(sink -> gw.register(new PayListener() {
            @Override public void onEvent(PayEvent event) { sink.next(event); }
            @Override public void onError(Throwable error) { sink.error(error); }
            @Override public void onClosed() { sink.complete(); }
        }));
    }

    public static void main(String[] args) {
        System.out.println("== 0. fire right after subscribe: is the listener there yet?");
        DemoGateway gw0 = new DemoGateway();
        var d0 = events(gw0).subscribe(e -> System.out.println("  got " + e));
        gw0.fire(new PayEvent("p-0", "AUTHORIZED"));
        d0.dispose();

        System.out.println("== 1. Flux.create without onDispose: no error, and the listener stays");
        DemoGateway gw1 = new DemoGateway();
        eventsWithoutOnDispose(gw1).take(1).subscribe();
        gw1.fire(new PayEvent("p-1", "AUTHORIZED"));
        System.out.println("  after take(1) finished: listeners=" + gw1.getListeners().size());

        System.out.println("== 2. take(2) cancels, and onDispose unregisters");
        DemoGateway gw = new DemoGateway();
        List<PayEvent> two = new ArrayList<>();
        events(gw).take(2).subscribe(two::add);
        gw.fire(new PayEvent("p-1", "AUTHORIZED")); gw.fire(new PayEvent("p-1", "CAPTURED")); gw.fire(new PayEvent("p-1", "SETTLED"));
        System.out.println("  got " + two);

        System.out.println("== 3. the SDK reports an error: sink.error fails the Flux");
        DemoGateway gw3 = new DemoGateway();
        events(gw3).subscribe(e -> System.out.println("  got " + e),
                e -> System.out.println("  subscriber got onError " + e.getClass().getSimpleName() + ": " + e.getMessage()));
        gw3.fire(new PayEvent("p-2", "AUTHORIZED"));
        gw3.fail(new IOException("gateway connection lost"));

        System.out.println("== 4. the SDK says it is done: sink.complete completes the Flux");
        DemoGateway gw4 = new DemoGateway();
        List<PayEvent> all = new ArrayList<>();
        events(gw4).subscribe(all::add, e -> {}, () -> System.out.println("  completed with " + all));
        gw4.fire(new PayEvent("p-3", "REFUNDED"));
        gw4.close();
    }
}
