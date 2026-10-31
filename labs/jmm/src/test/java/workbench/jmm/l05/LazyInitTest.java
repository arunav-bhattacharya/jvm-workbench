package workbench.jmm.l05;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.function.Supplier;

import static org.assertj.core.api.Assertions.assertThat;

class LazyInitTest {
    private static final int THREADS = 8;

    // starts the threads behind one latch so they all ask at the same moment, then joins them
    private static void collide(int threads, Runnable task) throws InterruptedException {
        CountDownLatch go = new CountDownLatch(1);
        List<Thread> ts = new ArrayList<>();
        for (int i = 0; i < threads; i++) {
            Thread t = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                task.run();
            }, "caller-" + i);
            t.start();
            ts.add(t);
        }
        go.countDown();
        for (Thread t : ts) t.join();
    }

    private static void pause(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    @Test
    @DisplayName("DoubleCheckedLazy runs a slow initializer exactly once when 8 threads ask at the same moment")
    void dclOnceUnderContention() throws InterruptedException {
        AtomicInteger runs = new AtomicInteger();
        DoubleCheckedLazy<Object> lazy = new DoubleCheckedLazy<>(() -> {
            runs.incrementAndGet();
            pause(50);   // a slow initializer widens the window for a race
            return new Object();
        });
        Set<Object> seen = ConcurrentHashMap.newKeySet();
        collide(THREADS, () -> seen.add(lazy.get()));
        assertThat(runs.get()).as("initializer runs").isEqualTo(1);
        assertThat(seen).as("distinct values handed out").hasSize(1);
    }

    @Test
    @DisplayName("DoubleCheckedLazy returns the same value on later calls without running the initializer again")
    void dclLaterCalls() {
        AtomicInteger runs = new AtomicInteger();
        DoubleCheckedLazy<StringBuilder> lazy = new DoubleCheckedLazy<>(() -> {
            runs.incrementAndGet();
            return new StringBuilder("ledger");
        });
        StringBuilder first = lazy.get();
        for (int i = 0; i < 1_000; i++) assertThat(lazy.get()).isSameAs(first);
        assertThat(runs.get()).isEqualTo(1);
    }

    @Test
    @DisplayName("DoubleCheckedLazy keeps its value in a volatile field (double-checked locking without volatile is broken)")
    void dclUsesVolatile() {
        boolean anyVolatile = false;
        for (Field f : DoubleCheckedLazy.class.getDeclaredFields()) {
            if (!Modifier.isStatic(f.getModifiers()) && Modifier.isVolatile(f.getModifiers())) anyVolatile = true;
        }
        assertThat(anyVolatile).as("a volatile instance field holds the value").isTrue();
    }

    @Test
    @DisplayName("CardBinTable.instance() is lazy, builds the table once under contention, and always returns the same table")
    void holderIdiom() throws InterruptedException {
        assertThat(CardBinTable.creations()).as("creations() alone must not build the table").isZero();
        Set<CardBinTable> seen = ConcurrentHashMap.newKeySet();
        collide(THREADS, () -> seen.add(CardBinTable.instance()));
        assertThat(CardBinTable.creations()).as("tables built").isEqualTo(1);
        assertThat(seen).as("distinct tables handed out").hasSize(1);
        assertThat(CardBinTable.instance().issuerFor("411111")).isEqualTo("Northwind Bank");
    }

    @Test
    @DisplayName("IssuerClients connects exactly once per issuer when 8 threads ask for 40 issuers at once")
    void oneClientPerIssuer() throws InterruptedException {
        Map<String, AtomicInteger> connects = new ConcurrentHashMap<>();
        AtomicLong connectionNumbers = new AtomicLong();
        IssuerClients clients = new IssuerClients(id -> {
            connects.computeIfAbsent(id, k -> new AtomicInteger()).incrementAndGet();
            pause(2);   // opening a connection takes a moment
            return new IssuerClient(id, connectionNumbers.incrementAndGet());
        });
        Map<String, Set<IssuerClient>> handedOut = new ConcurrentHashMap<>();
        collide(THREADS, () -> {
            for (int i = 0; i < 40; i++) {
                String id = "issuer-" + i;
                handedOut.computeIfAbsent(id, k -> ConcurrentHashMap.newKeySet()).add(clients.clientFor(id));
            }
        });
        assertThat(connects).hasSize(40);
        connects.forEach((id, n) -> assertThat(n.get()).as("connections opened for %s", id).isEqualTo(1));
        handedOut.forEach((id, set) -> assertThat(set).as("clients handed out for %s", id).hasSize(1));
    }
}
