package workbench.vthreads.l05;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.api.Assertions.assertTimeoutPreemptively;

class FailFastScopeTest {

    static String after(long ms, String value) throws InterruptedException {
        Thread.sleep(ms);
        return value;
    }

    @Test
    @DisplayName("join() returns when every subtask succeeded, and each handle gives its result")
    void allSucceed() throws Exception {
        try (FailFastScope scope = new FailFastScope()) {
            Supplier<String> bank = scope.fork(() -> after(60, "approved"));
            Supplier<String> stock = scope.fork(() -> after(30, "in stock"));
            Supplier<Integer> points = scope.fork(() -> 25);
            scope.join();
            assertThat(bank.get()).isEqualTo("approved");
            assertThat(stock.get()).isEqualTo("in stock");
            assertThat(points.get()).isEqualTo(25);
        }
    }

    @Test
    @DisplayName("Subtasks run on virtual threads, and join() waits for slow ones")
    void runsOnVirtualThreads() throws Exception {
        AtomicBoolean virtual = new AtomicBoolean();
        try (FailFastScope scope = new FailFastScope()) {
            Supplier<String> slow = scope.fork(() -> {
                virtual.set(Thread.currentThread().isVirtual());
                return after(200, "done");
            });
            scope.join();
            assertThat(slow.get()).isEqualTo("done");
        }
        assertThat(virtual).isTrue();
    }

    @Test
    @DisplayName("get() before join() throws IllegalStateException")
    void getBeforeJoin() throws Exception {
        try (FailFastScope scope = new FailFastScope()) {
            Supplier<String> stock = scope.fork(() -> "in stock");
            assertThatThrownBy(stock::get).isInstanceOf(IllegalStateException.class);
            scope.join();
            assertThat(stock.get()).isEqualTo("in stock");
        }
    }

    @Test
    @DisplayName("The first failure interrupts the siblings, and join() throws it at once as an ExecutionException")
    void failFast() {
        CountDownLatch slowWasInterrupted = new CountDownLatch(1);
        assertTimeoutPreemptively(Duration.ofSeconds(8), () -> {
            long t0 = System.nanoTime();
            try (FailFastScope scope = new FailFastScope()) {
                scope.fork(() -> {
                    try {
                        return after(10_000, "approved");      // a slow bank call nobody needs any more
                    } catch (InterruptedException e) {
                        slowWasInterrupted.countDown();
                        throw e;
                    }
                });
                scope.fork(() -> {
                    Thread.sleep(50);
                    throw new IllegalStateException("sold out");
                });
                assertThatThrownBy(scope::join)
                        .isInstanceOf(ExecutionException.class)
                        .cause().isInstanceOf(IllegalStateException.class).hasMessage("sold out");
            }
            long ms = (System.nanoTime() - t0) / 1_000_000;
            // the sibling sleeps 10 s; a fail-fast scope ends long before that (generous margin for busy machines)
            assertThat(ms).as("time until the scope closed (ms)").isLessThan(5_000);
        });
        assertThat(slowWasInterrupted.getCount()).as("slow sibling was interrupted").isZero();
    }

    @Test
    @DisplayName("After a failure, get() on the failed and on the cancelled subtask throws IllegalStateException")
    void handlesAfterFailure() throws Exception {
        try (FailFastScope scope = new FailFastScope()) {
            Supplier<String> slow = scope.fork(() -> after(10_000, "never"));
            Supplier<String> bad = scope.fork(() -> { throw new IllegalArgumentException("unknown product"); });
            assertThatThrownBy(scope::join).isInstanceOf(ExecutionException.class);
            assertThatThrownBy(slow::get).isInstanceOf(IllegalStateException.class);
            assertThatThrownBy(bad::get).isInstanceOf(IllegalStateException.class);
        }
    }

    @Test
    @DisplayName("close() without join() cancels unfinished subtasks and waits until their threads have ended")
    void closeCancelsAndWaits() {
        AtomicInteger running = new AtomicInteger();
        AtomicInteger cleanedUp = new AtomicInteger();
        assertTimeoutPreemptively(Duration.ofSeconds(8), () -> {
            try (FailFastScope scope = new FailFastScope()) {
                for (int i = 0; i < 3; i++) {
                    scope.fork(() -> {
                        running.incrementAndGet();
                        try {
                            new CountDownLatch(1).await(1, TimeUnit.MINUTES);   // blocks until interrupted
                            return "never";
                        } finally {
                            sleepUninterruptibly(150);             // cleanup that takes a while
                            cleanedUp.incrementAndGet();
                            running.decrementAndGet();
                        }
                    });
                }
                while (running.get() < 3) Thread.onSpinWait();     // all three are blocked now
            }
            // close() returned: every subtask was interrupted and has finished its cleanup
            assertThat(cleanedUp.get()).isEqualTo(3);
            assertThat(running.get()).isZero();
        });
    }

    @Test
    @DisplayName("A subtask forked after the scope was cancelled never runs, and its get() throws IllegalStateException")
    void noForkAfterFailure() {
        CountDownLatch siblingInterrupted = new CountDownLatch(1);
        AtomicBoolean lateRan = new AtomicBoolean();
        assertTimeoutPreemptively(Duration.ofSeconds(8), () -> {
            try (FailFastScope scope = new FailFastScope()) {
                scope.fork(() -> {
                    try {
                        return after(10_000, "approved");
                    } catch (InterruptedException e) {
                        siblingInterrupted.countDown();
                        throw e;
                    }
                });
                scope.fork(() -> { throw new IllegalStateException("sold out"); });
                // the sibling was interrupted, so the scope is cancelled by now
                assertThat(siblingInterrupted.await(5, TimeUnit.SECONDS)).as("sibling interrupted").isTrue();
                Supplier<String> late = scope.fork(() -> {
                    lateRan.set(true);
                    return "late";
                });
                assertThatThrownBy(scope::join).isInstanceOf(ExecutionException.class)
                        .cause().hasMessage("sold out");
                assertThatThrownBy(late::get).isInstanceOf(IllegalStateException.class);
            }
        });
        assertThat(lateRan).as("the late subtask ran").isFalse();
    }

    static void sleepUninterruptibly(long ms) {
        long end = System.nanoTime() + ms * 1_000_000;
        boolean interrupted = false;
        while (System.nanoTime() < end) {
            try {
                Thread.sleep(Math.max(1, (end - System.nanoTime()) / 1_000_000));
            } catch (InterruptedException e) {
                interrupted = true;
            }
        }
        if (interrupted) Thread.currentThread().interrupt();
    }
}
