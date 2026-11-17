package workbench.flows.l04;

import org.reactivestreams.Subscription;
import reactor.core.publisher.BaseSubscriber;
import reactor.core.publisher.BufferOverflowStrategy;
import reactor.core.publisher.Flux;

import java.util.ArrayList;
import java.util.List;
import java.util.function.UnaryOperator;

// Closest Java equivalent: Reactor's onBackpressure operators. The subscriber (the oven screen) requests
// one reading, holds it while 200 arrive, then requests the rest. Everything runs on the main thread.
public class DropPoliciesJava {

    static void policy(String label, UnaryOperator<Flux<Integer>> op) {
        List<Integer> seen = new ArrayList<>();
        Throwable[] error = new Throwable[1];
        BaseSubscriber<Integer> screen = new BaseSubscriber<>() {
            @Override protected void hookOnSubscribe(Subscription s) { request(1); }   // stuck on reading 1
            @Override protected void hookOnNext(Integer reading) { seen.add(reading); }
            @Override protected void hookOnError(Throwable t) { error[0] = t; }
        };
        op.apply(Flux.range(1, 200)).subscribe(screen);
        screen.request(Long.MAX_VALUE);                                              // unstuck
        String shown = seen.size() > 6
                ? seen.subList(0, 3) + " ... " + seen.subList(seen.size() - 2, seen.size())
                : seen.toString();
        System.out.printf("%-48s showed %3d readings: %s%s%n", label, seen.size(), shown,
                error[0] == null ? "" : "\n" + " ".repeat(49) + "ERROR " + error[0].getMessage());
    }

    public static void main(String[] args) {
        policy("onBackpressureBuffer(10, t -> {}, DROP_OLDEST)",
                f -> f.onBackpressureBuffer(10, t -> {}, BufferOverflowStrategy.DROP_OLDEST));
        policy("onBackpressureBuffer(10, t -> {}, DROP_LATEST)",
                f -> f.onBackpressureBuffer(10, t -> {}, BufferOverflowStrategy.DROP_LATEST));
        policy("onBackpressureLatest()", Flux::onBackpressureLatest);
        policy("onBackpressureDrop()", Flux::onBackpressureDrop);
        policy("onBackpressureBuffer(10)", f -> f.onBackpressureBuffer(10));
    }
}
