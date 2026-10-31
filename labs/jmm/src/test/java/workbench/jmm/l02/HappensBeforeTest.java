package workbench.jmm.l02;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.LongSupplier;

import static org.assertj.core.api.Assertions.assertThat;

class HappensBeforeTest {
    // Long enough for the JIT to compile a spinning loop. With no happens-before edge, a compiled loop may never stop.
    private static final long LET_THE_JIT_COMPILE_MS = 300;
    // A generous bound. Correct code finishes in milliseconds.
    private static final long GENEROUS_JOIN_MS = 5_000;

    private static Thread startDaemon(Runnable r, String name) {
        Thread t = new Thread(r, name);
        t.setDaemon(true);   // a stuck reader must not keep the test JVM alive
        t.start();
        return t;
    }

    @Test
    @DisplayName("LedgerTotals: a reader waiting in awaitAtLeast() sees the postings of 4 writer threads")
    void waitingReaderSeesTotal() throws InterruptedException {
        LedgerTotals totals = new LedgerTotals();
        long target = 4 * 50_000L;
        AtomicLong seen = new AtomicLong(-1);
        Thread reader = startDaemon(() -> seen.set(totals.awaitAtLeast(target)), "report");
        Thread.sleep(LET_THE_JIT_COMPILE_MS);

        List<Thread> writers = new ArrayList<>();
        for (int w = 0; w < 4; w++) {
            writers.add(startDaemon(() -> { for (int i = 0; i < 50_000; i++) totals.add(1); }, "poster-" + w));
        }
        for (Thread w : writers) w.join();
        reader.join(GENEROUS_JOIN_MS);

        assertThat(reader.isAlive())
                .as("the report thread is still waiting. Does total() share an edge with add()?")
                .isFalse();
        assertThat(seen.get()).isEqualTo(target);
        assertThat(totals.total()).isEqualTo(target);
    }

    @Test
    @DisplayName("IssuerReply: a request thread that is already waiting gets the reply the I/O thread completed")
    void waitingRequestGetsReply() throws InterruptedException {
        for (int round = 1; round <= 3; round++) {
            IssuerReply reply = new IssuerReply();
            AtomicReference<String> got = new AtomicReference<>();
            Thread request = startDaemon(() -> {
                try {
                    got.set(reply.awaitReply());
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }, "request-" + round);
            Thread.sleep(LET_THE_JIT_COMPILE_MS);
            reply.complete("AUTH-" + round, 120);
            request.join(GENEROUS_JOIN_MS);

            assertThat(request.isAlive())
                    .as("round %d: the request thread is still waiting after complete()", round)
                    .isFalse();
            assertThat(got.get()).isEqualTo("AUTH-" + round + " in 120 ms");
        }
    }

    @Test
    @DisplayName("IssuerReply: a reply completed before anyone waits is returned at once")
    void replyFirst() throws InterruptedException {
        IssuerReply reply = new IssuerReply();
        reply.complete("Z9", 85);
        assertThat(reply.awaitReply()).isEqualTo("Z9 in 85 ms");
    }

    @Test
    @DisplayName("PartitionReconciler: the total includes a slow partition, however long it takes")
    void includesSlowPartition() throws InterruptedException {
        CountDownLatch gate = new CountDownLatch(1);
        LongSupplier slow = () -> {
            try {
                gate.await();          // held closed by the test until reconcile() returns or 1 s passes
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            return 700;
        };
        List<LongSupplier> partitions = List.of(() -> 100, () -> 200, slow);

        AtomicLong total = new AtomicLong(-1);
        Thread caller = startDaemon(() -> {
            try {
                total.set(PartitionReconciler.reconcile(partitions));
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "caller");
        caller.join(1_000);   // a correct reconcile() is still waiting for the slow partition here
        gate.countDown();
        caller.join(GENEROUS_JOIN_MS);

        assertThat(caller.isAlive()).as("reconcile() should return once every partition is done").isFalse();
        assertThat(total.get()).as("total of 100 + 200 + 700").isEqualTo(1_000);
    }

    @Test
    @DisplayName("PartitionReconciler: 8 partitions of real work add up exactly")
    void eightPartitions() throws InterruptedException {
        List<LongSupplier> partitions = new ArrayList<>();
        long expected = 0;
        for (int p = 0; p < 8; p++) {
            int base = p * 1_000_000;
            partitions.add(() -> {
                long s = 0;
                for (int i = 0; i < 1_000_000; i++) s += base + i;
                return s;
            });
            for (int i = 0; i < 1_000_000; i++) expected += base + i;
        }
        assertThat(PartitionReconciler.reconcile(partitions)).isEqualTo(expected);
    }
}
