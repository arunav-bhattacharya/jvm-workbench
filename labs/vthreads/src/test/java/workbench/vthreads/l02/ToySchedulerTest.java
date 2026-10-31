package workbench.vthreads.l02;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;

class ToySchedulerTest {

    /**
     * A fiber written as a little state machine: a program counter says which sleep comes next.
     * Every time it is mounted it calls onMount, then asks to sleep for the next duration, or finishes.
     */
    static Fiber sleeper(Runnable onMount, long... sleeps) {
        int[] pc = {0};
        return () -> {
            onMount.run();
            return pc[0] < sleeps.length ? Step.sleep(sleeps[pc[0]++]) : Step.done();
        };
    }

    @Test
    @DisplayName("A fiber that waits 120 ms then 30 ms ends at virtual time 150 after 3 mounts")
    void oneFiber() {
        ToyScheduler s = new ToyScheduler();
        List<Long> mountedAt = new ArrayList<>();
        s.spawn(sleeper(() -> mountedAt.add(s.now()), 120, 30));
        int mounts = s.run();
        assertThat(mounts).isEqualTo(3);
        assertThat(mountedAt).containsExactly(0L, 120L, 150L);
        assertThat(s.now()).isEqualTo(150);
    }

    @Test
    @DisplayName("10,000 fibers that each wait 120 ms then 30 ms all finish at 150 ms, on one carrier thread")
    void waitsOverlap() {
        ToyScheduler s = new ToyScheduler();
        Set<Thread> carriers = new HashSet<>();
        int[] finished = {0};
        for (int i = 0; i < 10_000; i++) {
            int[] pc = {0};
            s.spawn(() -> {
                carriers.add(Thread.currentThread());
                return switch (pc[0]++) {
                    case 0 -> Step.sleep(120);   // call the card issuer
                    case 1 -> Step.sleep(30);    // write the ledger
                    default -> { finished[0]++; yield Step.done(); }
                };
            });
        }
        int mounts = s.run();
        assertThat(finished[0]).as("fibers that finished").isEqualTo(10_000);
        assertThat(mounts).as("mounts: 3 per fiber").isEqualTo(30_000);
        assertThat(s.now()).as("virtual time at the end").isEqualTo(150);
        assertThat(carriers).as("threads that ran fibers").containsExactly(Thread.currentThread());
    }

    @Test
    @DisplayName("Ready fibers run in the order they were spawned (FIFO)")
    void fifo() {
        ToyScheduler s = new ToyScheduler();
        List<String> order = new ArrayList<>();
        for (String name : List.of("a", "b", "c", "d")) s.spawn(sleeper(() -> order.add(name)));
        s.run();
        assertThat(order).containsExactly("a", "b", "c", "d");
        assertThat(s.now()).isZero();
    }

    @Test
    @DisplayName("A fiber that wakes earlier runs earlier, and sees the clock at its wake-up time")
    void earliestWakeFirst() {
        ToyScheduler s = new ToyScheduler();
        List<String> log = new ArrayList<>();
        s.spawn(sleeper(() -> log.add("slow@" + s.now()), 50));
        s.spawn(sleeper(() -> log.add("fast@" + s.now()), 10));
        s.run();
        assertThat(log).containsExactly("slow@0", "fast@0", "fast@10", "slow@50");
    }

    @Test
    @DisplayName("Fibers that wake at the same moment run in the order they went to sleep")
    void tiesKeepSleepOrder() {
        ToyScheduler s = new ToyScheduler();
        List<Integer> second = new ArrayList<>();
        for (int i = 0; i < 50; i++) {
            int id = i;
            int[] pc = {0};
            s.spawn(() -> {
                if (pc[0]++ == 1) second.add(id);
                return pc[0] == 1 ? Step.sleep(25) : Step.done();
            });
        }
        s.run();
        List<Integer> expected = new ArrayList<>();
        for (int i = 0; i < 50; i++) expected.add(i);
        assertThat(second).containsExactlyElementsOf(expected);
        assertThat(s.now()).isEqualTo(25);
    }

    @Test
    @DisplayName("A fiber can spawn more fibers while it runs, and they run too")
    void spawnWhileRunning() {
        ToyScheduler s = new ToyScheduler();
        List<String> log = new ArrayList<>();
        int[] pc = {0};
        s.spawn(() -> {
            if (pc[0]++ == 0) {
                for (int i = 0; i < 3; i++) {
                    int id = i;
                    s.spawn(sleeper(() -> log.add("child" + id + "@" + s.now()), 5));
                }
                return Step.sleep(100);
            }
            log.add("parent@" + s.now());
            return Step.done();
        });
        int mounts = s.run();
        assertThat(log).containsExactly("child0@0", "child1@0", "child2@0",
                "child0@5", "child1@5", "child2@5", "parent@100");
        assertThat(mounts).isEqualTo(2 + 3 * 2);
    }
}
