package workbench.reactive.l08;

import reactor.core.publisher.Flux;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/** One cold FX feed, shared five ways between dashboard A (starts now) and dashboard B (joins 250 ms later). */
public class HotColdDemo {
    static final AtomicInteger connections = new AtomicInteger();

    // a cold feed: every subscriber opens its own connection and gets rates from the start, one per 100 ms
    static Flux<String> rateFeed() {
        return Flux.interval(Duration.ofMillis(100)).take(5)
                .map(i -> "1.08" + i)
                .doOnSubscribe(s -> connections.incrementAndGet());
    }

    static void run(String title, Flux<String> feed) throws InterruptedException {
        connections.set(0);
        List<String> a = new CopyOnWriteArrayList<>();
        List<String> b = new CopyOnWriteArrayList<>();
        CountDownLatch done = new CountDownLatch(2);
        feed.doFinally(signal -> done.countDown()).subscribe(a::add);
        Thread.sleep(250);
        feed.doFinally(signal -> done.countDown()).subscribe(b::add);
        done.await(3, TimeUnit.SECONDS);
        System.out.printf("%-28s connections=%d%n%5sA=%s%n%5sB=%s%n", title, connections.get(), "", a, "", b);
    }

    public static void main(String[] args) throws InterruptedException {
        run("1. cold", rateFeed());
        run("2. share()", rateFeed().share());
        run("3. replay(1).refCount()", rateFeed().replay(1).refCount());
        run("4. cache()", rateFeed().cache());
        run("5. publish().autoConnect(2)", rateFeed().publish().autoConnect(2));
    }
}
