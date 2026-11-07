package workbench.reactive.l07;

import reactor.core.publisher.Flux;
import reactor.core.scheduler.Schedulers;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.function.Function;

/** A ticker that can't slow down (one tick per ms) and a screen that needs 10 ms per tick. */
public class OverflowDemo {
    static void run(String title, Function<Flux<Long>, Flux<Long>> strategy) {
        AtomicLong produced = new AtomicLong();
        List<Long> seen = new CopyOnWriteArrayList<>();
        String error = null;
        try {
            strategy.apply(Flux.interval(Duration.ofMillis(1)).doOnNext(produced::set))
                    .publishOn(Schedulers.single(), 1)          // the screen asks for one tick at a time
                    .doOnNext(tick -> sleep(10))                // and takes 10 ms to draw it
                    .take(20)
                    .doOnNext(seen::add)
                    .blockLast();
        } catch (RuntimeException e) {
            error = e.getMessage();
        }
        System.out.printf("%-28s ticker reached %3d, screen got %s%n", title, produced.get(), seen);
        if (error != null) {
            System.out.printf("%30sthen the error: %s%n", "", error);
        }
    }

    static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public static void main(String[] args) {
        run("1. no strategy", f -> f);
        AtomicInteger dropped = new AtomicInteger();
        run("2. onBackpressureDrop", f -> f.onBackpressureDrop(tick -> dropped.incrementAndGet()));
        System.out.printf("%30s(%d ticks dropped)%n", "", dropped.get());
        run("3. onBackpressureLatest", Flux::onBackpressureLatest);
        run("4. onBackpressureBuffer(10)", f -> f.onBackpressureBuffer(10));
        run("5. onBackpressureBuffer()", Flux::onBackpressureBuffer);
    }
}
