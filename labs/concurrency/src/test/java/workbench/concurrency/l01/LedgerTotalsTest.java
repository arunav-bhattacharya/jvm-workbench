package workbench.concurrency.l01;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.AbstractList;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.LongStream;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class LedgerTotalsTest {

    /** A list that remembers which threads read from it. */
    static final class Tracking extends AbstractList<Long> {
        final List<Long> data;
        final Set<Thread> readers = ConcurrentHashMap.newKeySet();

        Tracking(List<Long> data) { this.data = data; }

        @Override public Long get(int i) {
            readers.add(Thread.currentThread());
            return data.get(i);
        }

        @Override public int size() { return data.size(); }
    }

    private static List<Long> oneTo(int n) {
        return LongStream.rangeClosed(1, n).boxed().toList();
    }

    @Test
    @DisplayName("adds 1..1,000 with 4 workers")
    void addsUp() throws Exception {
        assertThat(LedgerTotals.total(oneTo(1_000), 4)).isEqualTo(500_500L);
    }

    @Test
    @DisplayName("handles a list that does not split evenly (10 amounts, 3 workers)")
    void unevenSlices() throws Exception {
        assertThat(LedgerTotals.total(oneTo(10), 3)).isEqualTo(55L);
        assertThat(LedgerTotals.total(oneTo(11), 4)).isEqualTo(66L);
    }

    @Test
    @DisplayName("does the adding on exactly N new threads, never on the caller")
    void usesWorkerThreads() throws Exception {
        Tracking amounts = new Tracking(oneTo(10_000));
        long total = LedgerTotals.total(amounts, 4);
        assertThat(total).isEqualTo(50_005_000L);
        assertThat(amounts.readers).as("threads that read amounts").hasSize(4);
        assertThat(amounts.readers).as("the caller must not read amounts").doesNotContain(Thread.currentThread());
    }

    @Test
    @DisplayName("never starts more threads than there are amounts")
    void noIdleThreads() throws Exception {
        Tracking amounts = new Tracking(List.of(100L, 250L, 999L));
        assertThat(LedgerTotals.total(amounts, 8)).isEqualTo(1_349L);
        assertThat(amounts.readers).hasSize(3);
    }

    @Test
    @DisplayName("an empty list totals 0, and fewer than 1 worker is rejected")
    void edgeCases() throws Exception {
        assertThat(LedgerTotals.total(List.of(), 4)).isZero();
        assertThatThrownBy(() -> LedgerTotals.total(oneTo(5), 0)).isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    @DisplayName("matches a plain loop on 1,000,000 random amounts with 8 workers")
    void bigList() throws Exception {
        Random random = new Random(42);
        List<Long> amounts = new ArrayList<>();
        long expected = 0;
        for (int i = 0; i < 1_000_000; i++) {
            long cents = 1 + random.nextInt(500_000);
            amounts.add(cents);
            expected += cents;
        }
        assertThat(LedgerTotals.total(amounts, 8)).isEqualTo(expected);
    }
}
