package workbench.jmm.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicLong;

import static org.assertj.core.api.Assertions.assertThat;

class PaymentSessionTest {
    private static final long LET_THE_JIT_COMPILE_MS = 300;
    private static final long GENEROUS_JOIN_MS = 5_000;
    private static final int THREADS = 8;

    private static Thread startDaemon(Runnable r, String name) {
        Thread t = new Thread(r, name);
        t.setDaemon(true);   // a stuck waiter must not keep the test JVM alive
        t.start();
        return t;
    }

    // starts all threads behind one latch so they really overlap, then joins them
    private static void collide(int threads, Runnable task) throws InterruptedException {
        CountDownLatch go = new CountDownLatch(1);
        List<Thread> ts = new ArrayList<>();
        for (int i = 0; i < threads; i++) {
            ts.add(startDaemon(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                task.run();
            }, "worker-" + i));
        }
        go.countDown();
        for (Thread t : ts) t.join();
    }

    @Test
    @DisplayName("status: a thread waiting in awaitStatus() sees the issuer callback's write")
    void statusIsVisible() throws InterruptedException {
        PaymentSession s = new PaymentSession(10_000);
        Thread waiter = startDaemon(() -> s.awaitStatus(PaymentSession.Status.CAPTURED), "waiter");
        Thread.sleep(LET_THE_JIT_COMPILE_MS);
        s.setStatus(PaymentSession.Status.AUTHORIZED);
        s.setStatus(PaymentSession.Status.CAPTURED);
        waiter.join(GENEROUS_JOIN_MS);
        assertThat(waiter.isAlive()).as("the waiter never saw CAPTURED").isFalse();
        assertThat(s.status()).isEqualTo(PaymentSession.Status.CAPTURED);
    }

    @Test
    @DisplayName("heartbeat: the watchdog waiting in awaitHeartbeatAfter() sees the new timestamp")
    void heartbeatIsVisible() throws InterruptedException {
        PaymentSession s = new PaymentSession(10_000);
        s.heartbeat(1_700_000_000_000L);
        AtomicLong seen = new AtomicLong();
        Thread watchdog = startDaemon(() -> seen.set(s.awaitHeartbeatAfter(1_700_000_000_000L)), "watchdog");
        Thread.sleep(LET_THE_JIT_COMPILE_MS);
        s.heartbeat(1_700_000_005_000L);
        watchdog.join(GENEROUS_JOIN_MS);
        assertThat(watchdog.isAlive()).as("the watchdog never saw the new heartbeat").isFalse();
        assertThat(seen.get()).isEqualTo(1_700_000_005_000L);
    }

    @Test
    @DisplayName("attempts: 8 retry threads x 200,000 attempts are all counted")
    void attemptsAddUp() throws InterruptedException {
        PaymentSession s = new PaymentSession(10_000);
        collide(THREADS, () -> { for (int i = 0; i < 200_000; i++) s.recordAttempt(); });
        assertThat(s.attempts()).isEqualTo(THREADS * 200_000);
    }

    @Test
    @DisplayName("money: racing captures and refunds never break refunded <= captured <= authorized")
    void invariantHolds() throws InterruptedException {
        long authorized = 200_000;
        PaymentSession s = new PaymentSession(authorized);
        AtomicLong capturedOk = new AtomicLong(), refundedOk = new AtomicLong();
        CountDownLatch go = new CountDownLatch(1);
        List<Thread> ts = new ArrayList<>();
        for (int i = 0; i < THREADS; i++) {
            boolean capturer = i % 2 == 0;
            ts.add(startDaemon(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                for (int k = 0; k < 100_000; k++) {
                    if (capturer) {
                        if (s.tryCapture(1)) capturedOk.incrementAndGet();
                    } else {
                        if (s.tryRefund(1)) refundedOk.incrementAndGet();
                    }
                }
            }, capturer ? "capture-" + i : "refund-" + i));
        }
        go.countDown();
        for (Thread t : ts) t.join();

        assertThat(s.capturedCents()).as("captured matches the successful captures").isEqualTo(capturedOk.get());
        assertThat(s.refundedCents()).as("refunded matches the successful refunds").isEqualTo(refundedOk.get());
        assertThat(s.capturedCents()).as("captured <= authorized").isLessThanOrEqualTo(authorized);
        assertThat(s.refundedCents()).as("refunded <= captured").isLessThanOrEqualTo(s.capturedCents());
        assertThat(s.capturedCents()).as("4 x 100,000 one-cent captures fill a 200,000 authorization").isEqualTo(authorized);
    }

    @Test
    @DisplayName("money: the limits hold for a single thread too")
    void limitsSingleThreaded() {
        PaymentSession s = new PaymentSession(1_000);
        assertThat(s.tryRefund(1)).as("nothing captured yet").isFalse();
        assertThat(s.tryCapture(700)).isTrue();
        assertThat(s.tryCapture(400)).as("would exceed the authorization").isFalse();
        assertThat(s.tryRefund(700)).isTrue();
        assertThat(s.tryRefund(1)).as("everything already refunded").isFalse();
        assertThat(s.capturedCents()).isEqualTo(700);
        assertThat(s.refundedCents()).isEqualTo(700);
    }
}
