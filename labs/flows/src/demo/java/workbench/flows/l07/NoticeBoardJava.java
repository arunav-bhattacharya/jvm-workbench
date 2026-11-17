package workbench.flows.l07;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.reactivestreams.Subscription;
import reactor.core.publisher.BaseSubscriber;
import reactor.core.publisher.Sinks;

// Java equivalent: an AtomicReference for the value and a Reactor sink for the stream.
// Reactor only conflates and de-duplicates if you ask for it with operators.
public class NoticeBoardJava {

    record MenuItem(String name, BigDecimal price) {}

    static final class Busy extends BaseSubscriber<String> {
        final List<String> got = new ArrayList<>();
        @Override protected void hookOnSubscribe(Subscription s) { request(1); }
        @Override protected void hookOnNext(String v) { got.add(v); }   // then busy: asks for nothing more
    }

    public static void main(String[] args) throws Exception {
        System.out.println("== A: equal values");
        System.out.println("  records with equal fields are equal: "
                + new MenuItem("soup of the day", new BigDecimal("4.50")).equals(new MenuItem("soup of the day", new BigDecimal("4.50"))));
        System.out.println("  4.50 equals 4.500? " + new BigDecimal("4.50").equals(new BigDecimal("4.500"))
                + "; compareTo == 0? " + (new BigDecimal("4.50").compareTo(new BigDecimal("4.500")) == 0));

        System.out.println("== B: tomato -> leek -> tomato while the subscriber is busy");
        for (boolean asStateFlow : new boolean[] {false, true}) {
            Sinks.Many<String> soup = Sinks.many().replay().latestOrDefault("tomato");
            Busy busy = new Busy();
            (asStateFlow ? soup.asFlux().onBackpressureLatest().distinctUntilChanged() : soup.asFlux()).subscribe(busy);
            soup.tryEmitNext("leek");
            soup.tryEmitNext("tomato");
            busy.request(Long.MAX_VALUE);   // no longer busy
            System.out.println("  " + (asStateFlow ? "with onBackpressureLatest().distinctUntilChanged(): " : "plain replay sink:                                  ") + busy.got);
        }

        System.out.println("== C: compareAndSet on AtomicReference compares references, not equals");
        AtomicReference<BigDecimal> price = new AtomicReference<>(new BigDecimal("10"));
        System.out.println("  cas(new 10, 11) = " + price.compareAndSet(new BigDecimal("10"), new BigDecimal("11")) + ", value " + price.get());

        System.out.println("== D: updateAndGet from 8 threads x 100,000 (REAL threads)");
        AtomicInteger calls = new AtomicInteger();
        AtomicReference<Integer> counter = new AtomicReference<>(0);
        List<Thread> threads = new ArrayList<>();
        for (int t = 0; t < 8; t++) {
            threads.add(Thread.ofPlatform().start(() -> {
                for (int i = 0; i < 100_000; i++) counter.updateAndGet(x -> { calls.incrementAndGet(); return x + 1; });
            }));
        }
        for (Thread t : threads) t.join();
        System.out.println("  value=" + counter.get() + ", the lambda ran " + calls.get() + " times");

        System.out.println("== E: currentSubscriberCount() is a number you read, with no history");
        Sinks.Many<Integer> events = Sinks.many().multicast().directBestEffort();
        System.out.println("  before: " + events.currentSubscriberCount());
        events.asFlux().subscribe().dispose();   // a visitor joins and leaves
        System.out.println("  after a visitor came and went: " + events.currentSubscriberCount());
    }
}
