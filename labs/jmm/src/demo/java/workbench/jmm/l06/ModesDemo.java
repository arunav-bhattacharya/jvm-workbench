package workbench.jmm.l06;

import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.IntConsumer;

/**
 * The store-buffering test from lesson 1, once per VarHandle access mode. Thread A runs
 * {@code x = 1; r1 = y;} and thread B runs {@code y = 1; r2 = x;}. Count the trials where both read 0.
 */
public class ModesDemo {
    static final class Pair { int x, y; }

    static final VarHandle X, Y;
    static {
        try {
            MethodHandles.Lookup lookup = MethodHandles.lookup();
            X = lookup.findVarHandle(Pair.class, "x", int.class);
            Y = lookup.findVarHandle(Pair.class, "y", int.class);
        } catch (ReflectiveOperationException e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    static final int TRIALS = 1 << 18;
    static final int BATCH = 32;

    public static void main(String[] args) throws InterruptedException {
        for (int run = 1; run <= 3; run++) {
            System.out.printf("run %d: both read 0 with plain %,6d | opaque %,6d | release/acquire %,6d | volatile %,d  (of %,d)%n",
                    run, plain(), opaque(), releaseAcquire(), volatileMode(), TRIALS);
        }
    }

    static int plain() throws InterruptedException {
        Pair[] s = pairs(); int[] r1 = new int[TRIALS], r2 = new int[TRIALS];
        race(i -> { X.set(s[i], 1); r1[i] = (int) Y.get(s[i]); },
             i -> { Y.set(s[i], 1); r2[i] = (int) X.get(s[i]); });
        return bothZero(r1, r2);
    }

    static int opaque() throws InterruptedException {
        Pair[] s = pairs(); int[] r1 = new int[TRIALS], r2 = new int[TRIALS];
        race(i -> { X.setOpaque(s[i], 1); r1[i] = (int) Y.getOpaque(s[i]); },
             i -> { Y.setOpaque(s[i], 1); r2[i] = (int) X.getOpaque(s[i]); });
        return bothZero(r1, r2);
    }

    static int releaseAcquire() throws InterruptedException {
        Pair[] s = pairs(); int[] r1 = new int[TRIALS], r2 = new int[TRIALS];
        race(i -> { X.setRelease(s[i], 1); r1[i] = (int) Y.getAcquire(s[i]); },
             i -> { Y.setRelease(s[i], 1); r2[i] = (int) X.getAcquire(s[i]); });
        return bothZero(r1, r2);
    }

    static int volatileMode() throws InterruptedException {
        Pair[] s = pairs(); int[] r1 = new int[TRIALS], r2 = new int[TRIALS];
        race(i -> { X.setVolatile(s[i], 1); r1[i] = (int) Y.getVolatile(s[i]); },
             i -> { Y.setVolatile(s[i], 1); r2[i] = (int) X.getVolatile(s[i]); });
        return bothZero(r1, r2);
    }

    static Pair[] pairs() {
        Pair[] s = new Pair[TRIALS];
        for (int i = 0; i < TRIALS; i++) s[i] = new Pair();
        return s;
    }

    // Runs a(i) and b(i) for every trial on two threads. A small spin barrier every BATCH trials
    // keeps the two threads on the same trial at about the same moment.
    static void race(IntConsumer a, IntConsumer b) throws InterruptedException {
        AtomicInteger doneA = new AtomicInteger(), doneB = new AtomicInteger();
        Thread ta = new Thread(() -> runSide(a, doneA, doneB));
        Thread tb = new Thread(() -> runSide(b, doneB, doneA));
        ta.start(); tb.start();
        ta.join(); tb.join();
    }

    static void runSide(IntConsumer side, AtomicInteger mine, AtomicInteger other) {
        for (int batch = 0; batch < TRIALS / BATCH; batch++) {
            mine.set(batch);
            while (other.get() < batch) Thread.onSpinWait();   // wait for the other thread
            for (int i = batch * BATCH; i < (batch + 1) * BATCH; i++) side.accept(i);
        }
    }

    static int bothZero(int[] r1, int[] r2) {
        int n = 0;
        for (int i = 0; i < r1.length; i++) if (r1[i] == 0 && r2[i] == 0) n++;
        return n;
    }
}
