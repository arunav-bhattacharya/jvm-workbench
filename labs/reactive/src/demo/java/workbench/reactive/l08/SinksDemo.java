package workbench.reactive.l08;

import reactor.core.publisher.Sinks;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.BiConsumer;

/** Sinks push values into Reactor from ordinary code. Who receives what, and what happens with 8 threads? */
public class SinksDemo {
    public static void main(String[] args) throws InterruptedException {
        Sinks.Many<Integer> multicast = Sinks.many().multicast().onBackpressureBuffer();
        List<Integer> early = new CopyOnWriteArrayList<>();
        List<Integer> late = new CopyOnWriteArrayList<>();
        multicast.tryEmitNext(10);                            // nobody is subscribed yet
        multicast.asFlux().subscribe(early::add);
        multicast.tryEmitNext(1);
        multicast.tryEmitNext(2);
        multicast.asFlux().subscribe(late::add);
        multicast.tryEmitNext(3);
        System.out.println("1. multicast:        early=" + early + "  late=" + late);

        afterEveryoneLeft("onBackpressureBuffer()", Sinks.many().multicast().onBackpressureBuffer());
        afterEveryoneLeft("directBestEffort()", Sinks.many().multicast().directBestEffort());

        Sinks.Many<Integer> replay = Sinks.many().replay().limit(2);
        replay.tryEmitNext(1);
        replay.tryEmitNext(2);
        replay.tryEmitNext(3);
        List<Integer> lateReplay = new CopyOnWriteArrayList<>();
        replay.asFlux().subscribe(lateReplay::add);
        System.out.println("3. replay().limit(2): late=" + lateReplay);

        Sinks.Many<Integer> unicast = Sinks.many().unicast().onBackpressureBuffer();
        unicast.asFlux().subscribe();
        unicast.asFlux().subscribe(v -> { }, e -> System.out.println("4. unicast, second subscriber: " + e.getMessage()));

        race("5. tryEmitNext from 8 threads", (sink, i) -> {
            if (sink.tryEmitNext(i).isFailure()) failures.incrementAndGet();
        });
        race("6. emitNext + busyLooping", (sink, i) ->
                sink.emitNext(i, Sinks.EmitFailureHandler.busyLooping(Duration.ofSeconds(1))));
    }

    static void afterEveryoneLeft(String flavour, Sinks.Many<Integer> sink) {
        sink.asFlux().subscribe().dispose();                      // the only subscriber leaves
        List<String> next = new CopyOnWriteArrayList<>();
        sink.asFlux().subscribe(v -> next.add("got " + v), e -> next.add("error"), () -> next.add("completed"));
        sink.tryEmitNext(42);
        System.out.printf("2. %-22s after everyone left, a new subscriber %s%n", flavour, next);
    }

    static final AtomicInteger failures = new AtomicInteger();

    static void race(String title, BiConsumer<Sinks.Many<Integer>, Integer> emit) throws InterruptedException {
        Sinks.Many<Integer> sink = Sinks.many().multicast().onBackpressureBuffer();
        AtomicInteger received = new AtomicInteger();
        sink.asFlux().subscribe(v -> received.incrementAndGet());
        failures.set(0);
        CountDownLatch go = new CountDownLatch(1);
        Thread[] threads = new Thread[8];
        for (int t = 0; t < threads.length; t++) {
            threads[t] = new Thread(() -> {
                try {
                    go.await();
                } catch (InterruptedException e) {
                    return;
                }
                for (int i = 0; i < 10_000; i++) emit.accept(sink, i);
            });
            threads[t].start();
        }
        go.countDown();
        for (Thread t : threads) t.join();
        System.out.printf("%-32s received %,d of 80,000 (%,d emits failed)%n", title, received.get(), failures.get());
    }
}
