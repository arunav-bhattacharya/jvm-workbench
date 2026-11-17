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

    static void run(String label, Flux<String> loaves, boolean serveAboveTheNet) {
        List<String> got = new ArrayList<>();
        String[] caught = {"nothing"};
        Flux<String> pipeline = serveAboveTheNet ? loaves.doOnNext(CatchNetJava::serve) : loaves;
        pipeline = pipeline.onErrorResume(e -> { caught[0] = e.getClass().getSimpleName() + ": " + e.getMessage(); return Mono.just("crackers"); });
        if (!serveAboveTheNet) pipeline = pipeline.doOnNext(CatchNetJava::serve);
        String callerSaw = "nothing";
        try {
            pipeline.doOnNext(got::add).blockLast();
        } catch (RuntimeException e) {
            callerSaw = e.getClass().getSimpleName() + ": " + e.getMessage();
        }
        System.out.printf("%-46s got %-24s net caught %-58s caller saw %s%n", label, got, caught[0], callerSaw);
    }

    static void serve(String loaf) {   // the diner drops the second plate
        if (loaf.equals("fresh loaf")) throw new IllegalStateException("the diner dropped the plate");
    }

    public static void main(String[] args) throws InterruptedException {
        run("the bakery call fails with IOException", Flux.concat(Flux.just("old loaf"), Flux.error(new IOException("line dropped"))), false);
        run("the bakery is slow: timeout(50 ms) above the net",
                Flux.concat(Flux.just("old loaf"), Mono.delay(Duration.ofMillis(100)).thenReturn("fresh loaf")).timeout(Duration.ofMillis(50)), false);
        run("serving below the net", Flux.just("old loaf", "fresh loaf"), false);
        run("serving above the net (doOnNext first)", Flux.just("old loaf", "fresh loaf"), true);

        String[] caught = {"nothing"};
        Disposable subscription = Flux.concat(Flux.just("old loaf"), Flux.<String>never())
                .onErrorResume(e -> { caught[0] = e.toString(); return Mono.empty(); })
                .doFinally(signal -> System.out.printf("%-46s doFinally %s, net caught %s%n", "the subscriber cancels", signal, caught[0]))
                .subscribe();
        Thread.sleep(20);
        subscription.dispose();
    }
}
