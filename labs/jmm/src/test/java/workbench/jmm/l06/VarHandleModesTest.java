package workbench.jmm.l06;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.lang.invoke.VarHandle;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.IntConsumer;

import static org.assertj.core.api.Assertions.assertThat;

class VarHandleModesTest {
    private static final int HANDOFFS = 100_000;
    // Long enough for the JIT to compile a spinning loop.
    private static final long LET_THE_JIT_COMPILE_MS = 300;
    // A generous bound. A correct handoff or spin loop is done in a small fraction of this.
    private static final long GENEROUS_JOIN_MS = 20_000;

    private static Settlement settlement(long id) {
        Settlement s = new Settlement();
        s.id = id;
        s.amountCents = id * 7;
        s.currency = currencyFor(id);
        return s;
    }

    private static String currencyFor(long id) {
        return id % 2 == 0 ? "EUR" : "USD";
    }

    private static Thread daemon(Runnable r, String name) {
        Thread t = new Thread(r, name);
        t.setDaemon(true);   // a stuck spinner must not keep the test JVM alive
        return t;
    }

    // parks every thread at a start line, releases them together, then joins them
    private static void collide(int threads, IntConsumer task) throws InterruptedException {
        CountDownLatch ready = new CountDownLatch(threads);
        CountDownLatch go = new CountDownLatch(1);
        List<Thread> ts = new ArrayList<>();
        for (int i = 0; i < threads; i++) {
            int me = i;
            Thread t = new Thread(() -> {
                ready.countDown();
                try { go.await(); } catch (InterruptedException e) { return; }
                task.accept(me);
            }, "caller-" + i);
            t.start();
            ts.add(t);
        }
        ready.await();
        go.countDown();
        for (Thread t : ts) t.join();
    }

    @Test
    @DisplayName("SettlementSlot.offer fills an empty slot and refuses a full one")
    void offerRefusesFull() {
        SettlementSlot slot = new SettlementSlot();
        Settlement first = settlement(1);
        assertThat(slot.offer(first)).as("offer to an empty slot").isTrue();
        assertThat(slot.offer(settlement(2))).as("offer to a full slot").isFalse();
        assertThat(slot.poll()).as("the slot keeps the first settlement").isSameAs(first);
    }

    @Test
    @DisplayName("SettlementSlot.poll returns null when empty, and taking a settlement empties the slot")
    void pollEmpties() {
        SettlementSlot slot = new SettlementSlot();
        assertThat(slot.poll()).as("poll on a new slot").isNull();
        Settlement s = settlement(1);
        slot.offer(s);
        assertThat(slot.poll()).isSameAs(s);
        assertThat(slot.poll()).as("a second poll").isNull();
        assertThat(slot.offer(settlement(2))).as("offer after the consumer took the first one").isTrue();
    }

    @Test
    @DisplayName("A producer and a consumer hand over 100,000 settlements in order, each one whole")
    void handoff() throws InterruptedException {
        SettlementSlot slot = new SettlementSlot();
        AtomicReference<String> problem = new AtomicReference<>();
        Thread producer = daemon(() -> {
            try {
                for (long id = 1; id <= HANDOFFS; id++) {
                    Settlement s = settlement(id);         // plain writes to the fields...
                    while (!slot.offer(s)) Thread.yield(); // ...then the handoff
                }
            } catch (Throwable e) {
                problem.compareAndSet(null, "producer threw " + e);
            }
        }, "producer");
        Thread consumer = daemon(() -> {
            try {
                for (long id = 1; id <= HANDOFFS; id++) {
                    Settlement s;
                    while ((s = slot.poll()) == null) Thread.yield();
                    if (s.id != id || s.amountCents != id * 7 || !currencyFor(id).equals(s.currency)) {
                        problem.compareAndSet(null, "expected settlement " + id + " but got id=" + s.id
                                + ", amountCents=" + s.amountCents + ", currency=" + s.currency);
                        return;
                    }
                }
            } catch (Throwable e) {
                problem.compareAndSet(null, "consumer threw " + e);
            }
        }, "consumer");
        producer.start();
        consumer.start();
        consumer.join(GENEROUS_JOIN_MS);
        producer.join(1_000);
        assertThat(problem.get()).as("first problem seen").isNull();
        assertThat(consumer.isAlive()).as("the consumer is still waiting for a settlement").isFalse();
        assertThat(producer.isAlive()).as("the producer is still waiting for an empty slot").isFalse();
        assertThat(slot.poll()).as("nothing left in the slot").isNull();
    }

    @Test
    @DisplayName("KillSwitch.trip returns true for the first caller only, and the first reason sticks")
    void firstTripWins() {
        KillSwitch ks = new KillSwitch();
        assertThat(ks.isTripped()).as("a new switch").isFalse();
        assertThat(ks.reason()).isNull();
        assertThat(ks.trip("issuer 4021 timed out")).as("first trip").isTrue();
        assertThat(ks.trip("fraud score spike")).as("second trip").isFalse();
        assertThat(ks.isTripped()).isTrue();
        assertThat(ks.reason()).isEqualTo("issuer 4021 timed out");
    }

    @Test
    @DisplayName("8 threads trip the switch at the same moment: exactly one wins, and all of them read the winner's reason")
    void exactlyOneWinner() throws InterruptedException {
        for (int round = 1; round <= 50; round++) {
            KillSwitch ks = new KillSwitch();
            AtomicInteger wins = new AtomicInteger();
            Set<String> reasonsSeen = ConcurrentHashMap.newKeySet();
            collide(8, me -> {
                if (ks.trip("reason-" + me)) wins.incrementAndGet();
                reasonsSeen.add(String.valueOf(ks.reason()));
            });
            assertThat(wins.get()).as("round %d: callers that got true", round).isEqualTo(1);
            assertThat(reasonsSeen).as("round %d: reasons the callers read", round).hasSize(1);
        }
    }

    @Test
    @DisplayName("A request thread spinning on isTripped() sees the trip, even once the JIT has compiled its loop")
    void spinnerSeesTrip() throws InterruptedException {
        for (int round = 1; round <= 3; round++) {
            KillSwitch ks = new KillSwitch();
            Thread spinner = daemon(() -> {
                while (!ks.isTripped()) {
                    // an authorization would run here
                }
            }, "request-" + round);
            spinner.start();
            Thread.sleep(LET_THE_JIT_COMPILE_MS);
            ks.trip("issuer 4021 timed out");
            spinner.join(5_000);
            assertThat(spinner.isAlive())
                    .as("round %d: the request thread still thinks the switch is off. Can it see the write?", round)
                    .isFalse();
        }
    }

    @Test
    @DisplayName("SettlementSlot and KillSwitch reach their fields through a static final VarHandle, with no volatile field and no synchronized method")
    void usesVarHandles() {
        for (Class<?> c : List.of(SettlementSlot.class, KillSwitch.class)) {
            boolean hasHandle = Arrays.stream(c.getDeclaredFields()).anyMatch(f -> f.getType() == VarHandle.class
                    && Modifier.isStatic(f.getModifiers()) && Modifier.isFinal(f.getModifiers()));
            assertThat(hasHandle).as("%s declares a static final VarHandle", c.getSimpleName()).isTrue();
            assertThat(Arrays.stream(c.getDeclaredFields()).filter(f -> Modifier.isVolatile(f.getModifiers())).map(Field::getName))
                    .as("volatile fields in %s (put the mode on each access instead)", c.getSimpleName()).isEmpty();
            assertThat(Arrays.stream(c.getDeclaredMethods()).filter(m -> Modifier.isSynchronized(m.getModifiers())).map(Method::getName))
                    .as("synchronized methods in %s", c.getSimpleName()).isEmpty();
        }
    }
}
