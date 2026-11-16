package workbench.flows.l06;

import reactor.core.Disposable;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.io.IOException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

// Closest Java equivalent of catch: Reactor's onErrorResume, which also handles only what comes from above it.
public class CatchNetJava {

    static void run(String label, Flux<Double> rates, boolean saveAboveTheNet) {
        List<Double> got = new ArrayList<>();
        String[] caught = {"nothing"};
        Flux<Double> pipeline = saveAboveTheNet ? rates.doOnNext(CatchNetJava::save) : rates;
        pipeline = pipeline.onErrorResume(e -> { caught[0] = e.getClass().getSimpleName() + ": " + e.getMessage(); return Mono.just(-1.0); });
        if (!saveAboveTheNet) pipeline = pipeline.doOnNext(CatchNetJava::save);
        String callerSaw = "nothing";
        try {
            pipeline.doOnNext(got::add).blockLast();
        } catch (RuntimeException e) {
            callerSaw = e.getClass().getSimpleName() + ": " + e.getMessage();
        }
        System.out.printf("%-44s got %-12s net caught %-58s caller saw %s%n", label, got, caught[0], callerSaw);
    }

    static void save(double rate) {   // the ledger write fails on the second rate
        if (rate == 0.93) throw new IllegalStateException("ledger write failed");
    }

    public static void main(String[] args) throws InterruptedException {
        run("provider fails with IOException", Flux.concat(Flux.just(0.92), Flux.error(new IOException("provider reset"))), false);
        run("provider is slow: timeout(50 ms) above the net",
                Flux.concat(Flux.just(0.92), Mono.delay(Duration.ofMillis(100)).thenReturn(0.95)).timeout(Duration.ofMillis(50)), false);
        run("ledger write below the net", Flux.just(0.92, 0.93), false);
        run("ledger write above the net (doOnNext first)", Flux.just(0.92, 0.93), true);

        String[] caught = {"nothing"};
        Disposable subscription = Flux.concat(Flux.just(0.92), Flux.<Double>never())
                .onErrorResume(e -> { caught[0] = e.toString(); return Mono.empty(); })
                .doFinally(signal -> System.out.printf("%-44s doFinally %s, net caught %s%n", "the subscriber cancels", signal, caught[0]))
                .subscribe();
        Thread.sleep(20);
        subscription.dispose();
    }
}
