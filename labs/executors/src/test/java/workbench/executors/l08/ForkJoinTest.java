package workbench.executors.l08;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ForkJoinPool;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import static org.assertj.core.api.Assertions.assertThat;

class ForkJoinTest {
    /** 2.9% plus 30 cents, rounded down: cheap CPU work. */
    private static final FeeModel CARD_FEE = amount -> amount * 29 / 1_000 + 30;

    private final ForkJoinPool pool = new ForkJoinPool(4);
    private final AtomicInteger ids = new AtomicInteger();
    private final ExecutorService io = Executors.newFixedThreadPool(8, r -> {
        Thread t = new Thread(r, "bin-io-" + ids.incrementAndGet());
        t.setDaemon(true);
        return t;
    });

    @AfterEach
    void stop() {
        pool.shutdownNow();
        io.shutdownNow();
    }

    private static long[] ledger(int n) {
        long[] amounts = new long[n];
        for (int i = 0; i < n; i++) amounts[i] = 100 + (i * 7919L) % 250_000;   // 1.00 to 2,501.00
        return amounts;
    }

    private static long sequentialFees(long[] amounts) {
        long sum = 0;
        for (long a : amounts) sum += CARD_FEE.feeCents(a);
        return sum;
    }

    @Test
    @DisplayName("LedgerFees totals the fees of 2,000,000 entries exactly")
    void totalsALargeLedger() {
        long[] amounts = ledger(2_000_000);
        assertThat(pool.invoke(new LedgerFees(amounts, CARD_FEE, 10_000))).isEqualTo(sequentialFees(amounts));
    }

    @Test
    @DisplayName("LedgerFees handles empty, tiny and threshold-sized ledgers")
    void handlesEdgeSizes() {
        for (int n : new int[] {0, 1, 2, 999, 1_000, 1_001, 4_097}) {
            long[] amounts = ledger(n);
            assertThat(pool.invoke(new LedgerFees(amounts, CARD_FEE, 1_000))).as("n = " + n).isEqualTo(sequentialFees(amounts));
        }
    }

    @Test
    @DisplayName("LedgerFees runs its two halves at the same time")
    void runsHalvesInParallel() {
        // exactly two leaves of 1,000 entries; the first fee on each thread waits for a second thread to arrive.
        // That only works if one half is forked and the other is computed while it runs.
        CyclicBarrier twoHalves = new CyclicBarrier(2);
        Set<Thread> arrived = ConcurrentHashMap.newKeySet();
        FeeModel meeting = amount -> {
            if (arrived.add(Thread.currentThread())) {
                try {
                    twoHalves.await(5, TimeUnit.SECONDS);
                } catch (InterruptedException | BrokenBarrierException | TimeoutException e) {
                    throw new IllegalStateException("the two halves did not run at the same time", e);
                }
            }
            return CARD_FEE.feeCents(amount);
        };
        long[] amounts = ledger(2_000);
        assertThat(pool.invoke(new LedgerFees(amounts, meeting, 1_000))).isEqualTo(sequentialFees(amounts));
    }

    @Test
    @DisplayName("flaggedIds returns every flagged id, in the original order")
    void flaggedIdsKeepsEverythingInOrder() {
        List<Payment> payments = IntStream.range(0, 200_000)
                .mapToObj(i -> new Payment("pay-" + i, i % 7 == 0 ? 900_000 : 1_000))
                .toList();
        List<String> expected = payments.stream().filter(p -> p.amountCents() > 500_000).map(Payment::id).toList();
        for (int run = 0; run < 3; run++) {
            assertThat(ParallelPitfalls.flaggedIds(payments, 500_000)).as("run " + run).isEqualTo(expected);
        }
    }

    @Test
    @DisplayName("issuers runs the blocking lookups on the io executor, not the common pool")
    void issuersUsesIo() {
        Set<String> threads = ConcurrentHashMap.newKeySet();
        BinLookup lookup = bin -> {
            threads.add(Thread.currentThread().getName());
            return "bank-" + bin.charAt(0);
        };
        List<String> bins = List.of("411111", "522222", "433333", "544444", "455555", "366666");

        Map<String, String> result = ParallelPitfalls.issuers(bins, lookup, io);

        assertThat(result).isEqualTo(bins.stream().collect(Collectors.toMap(Function.identity(), b -> "bank-" + b.charAt(0))));
        assertThat(threads).isNotEmpty().allMatch(name -> name.startsWith("bin-io-"), "runs on bin-io-* threads");
    }

    @Test
    @DisplayName("issuers runs 8 lookups at the same time on an 8-thread io pool")
    void issuersRunsAllAtOnce() {
        // every lookup waits until all eight are in flight; the common pool is too small for that on most machines
        CyclicBarrier allEight = new CyclicBarrier(8);
        BinLookup lookup = bin -> {
            try {
                allEight.await(5, TimeUnit.SECONDS);
            } catch (InterruptedException | BrokenBarrierException | TimeoutException e) {
                throw new IllegalStateException("the lookups did not run at the same time", e);
            }
            return "bank-" + bin;
        };
        List<String> bins = IntStream.range(0, 8).mapToObj(i -> "4" + i + "0000").toList();
        assertThat(ParallelPitfalls.issuers(bins, lookup, io)).hasSize(8).containsEntry("400000", "bank-400000");
    }
}
