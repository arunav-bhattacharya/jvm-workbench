package workbench.concurrency.l12;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicIntegerArray;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.api.Assertions.assertTimeoutPreemptively;

class ClassicProblemsTest {

    private static List<List<String>> records(int producers, int each) {
        List<List<String>> all = new ArrayList<>();
        for (int p = 0; p < producers; p++) {
            List<String> mine = new ArrayList<>();
            for (int i = 0; i < each; i++) mine.add("settle-" + p + "-" + i);
            all.add(mine);
        }
        return all;
    }

    // ---------- SettlementPipeline ----------

    @Test
    @DisplayName("Pipeline: 3 producers, 4 consumers, a queue of 8: every record is processed exactly once")
    void everyRecordOnce() {
        Map<String, AtomicInteger> seen = new ConcurrentHashMap<>();
        int count = assertTimeoutPreemptively(Duration.ofSeconds(10), () ->
                SettlementPipeline.run(records(3, 5_000), 4, 8, r -> seen.computeIfAbsent(r, k -> new AtomicInteger()).incrementAndGet()),
                "run() never returned: does every consumer get its own pill?");
        assertThat(count).isEqualTo(15_000);
        assertThat(seen).hasSize(15_000);
        assertThat(seen.values()).allMatch(n -> n.get() == 1, "processed exactly once");
    }

    @Test
    @DisplayName("Pipeline: run() returns only after every consumer has finished processing")
    void returnsAfterConsumersStop() {
        AtomicBoolean returned = new AtomicBoolean();
        AtomicInteger late = new AtomicInteger();
        assertTimeoutPreemptively(Duration.ofSeconds(10), () -> {
            SettlementPipeline.run(records(2, 300), 3, 4, r -> {
                try { Thread.sleep(1); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                if (returned.get()) late.incrementAndGet();
            });
            returned.set(true);
        }, "run() never returned: does every consumer get its own pill?");
        try { Thread.sleep(100); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        assertThat(late.get()).as("records processed after run() returned").isZero();
    }

    @Test
    @DisplayName("Pipeline: a real record whose text looks like a pill is still processed")
    void lookalikeRecordProcessed() {
        List<List<String>> input = List.of(List.of("settle-1", "PILL", "POISON", "settle-2"), List.of("settle-3"));
        List<String> processed = new java.util.concurrent.CopyOnWriteArrayList<>();
        int count = assertTimeoutPreemptively(Duration.ofSeconds(10), () -> SettlementPipeline.run(input, 2, 2, processed::add));
        assertThat(count).isEqualTo(5);
        assertThat(processed).containsExactlyInAnyOrder("settle-1", "PILL", "POISON", "settle-2", "settle-3");
    }

    // ---------- DiningTable ----------

    private static void dineAll(DiningTable table, int meals, Runnable eat) throws InterruptedException {
        List<Thread> philosophers = new ArrayList<>();
        for (int s = 0; s < table.seats(); s++) {
            int seat = s;
            Thread t = new Thread(() -> table.dine(seat, meals, eat), "philosopher-" + s);
            t.setDaemon(true);                 // a deadlocked philosopher must not keep the JVM alive
            t.start();
            philosophers.add(t);
        }
        for (Thread t : philosophers) t.join();
    }

    @Test
    @DisplayName("DiningTable: 5 philosophers x 100 meals all finish (no deadlock)")
    void fiveFinish() {
        DiningTable table = new DiningTable(5);
        AtomicInteger meals = new AtomicInteger();
        assertTimeoutPreemptively(Duration.ofSeconds(15), () -> dineAll(table, 100, meals::incrementAndGet),
                "the philosophers deadlocked: is there a fork order that everyone follows?");
        assertThat(meals.get()).isEqualTo(500);
    }

    @Test
    @DisplayName("DiningTable: two neighbours never eat at the same time")
    void neighboursNeverEatTogether() {
        DiningTable table = new DiningTable(5);
        AtomicIntegerArray eating = new AtomicIntegerArray(5);
        AtomicInteger clashes = new AtomicInteger();
        AtomicInteger seatOf = new AtomicInteger();
        ThreadLocal<Integer> mySeat = ThreadLocal.withInitial(() -> Integer.parseInt(Thread.currentThread().getName().substring(12)));
        assertTimeoutPreemptively(Duration.ofSeconds(15), () -> dineAll(table, 60, () -> {
            int s = mySeat.get();
            eating.set(s, 1);
            if (eating.get((s + 1) % 5) == 1 || eating.get((s + 4) % 5) == 1) clashes.incrementAndGet();
            Thread.onSpinWait();
            eating.set(s, 0);
            seatOf.incrementAndGet();
        }), "the philosophers deadlocked: is there a fork order that everyone follows?");
        assertThat(clashes.get()).as("meals eaten while a neighbour was also eating").isZero();
        assertThat(seatOf.get()).isEqualTo(300);
    }

    @Test
    @DisplayName("DiningTable: a table for two works, and a table for one is rejected")
    void tableForTwo() {
        DiningTable table = new DiningTable(2);
        AtomicInteger meals = new AtomicInteger();
        assertTimeoutPreemptively(Duration.ofSeconds(15), () -> dineAll(table, 200, meals::incrementAndGet),
                "two philosophers deadlocked");
        assertThat(meals.get()).isEqualTo(400);
        assertThatThrownBy(() -> new DiningTable(1)).isInstanceOf(IllegalArgumentException.class);
    }
}
