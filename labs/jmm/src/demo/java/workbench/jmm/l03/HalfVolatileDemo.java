package workbench.jmm.l03;

import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.IntConsumer;

/**
 * The store-buffering test from lesson 1 of this track, three ways: no volatile, only x volatile,
 * both fields volatile. Thread A runs {@code x = 1; r1 = y;} and thread B runs {@code y = 1; r2 = x;}.
 * Counts the trials where both threads read 0.
 */
public class HalfVolatileDemo {
    static final class Plain { int x, y; }
    static final class XOnly { volatile int x; int y; }
    static final class Both { volatile int x, y; }

    static final int TRIALS = 1 << 19;
    static final int BATCH = 32;

    public static void main(String[] args) throws InterruptedException {
        for (int run = 1; run <= 3; run++) {
            System.out.printf("run %d: both read 0 in  plain: %,7d   only x volatile: %,7d   both volatile: %,d%n",
                    run, plain(), xOnly(), both());
        }
    }

    static int plain() throws InterruptedException {
        Plain[] s = new Plain[TRIALS];
        for (int i = 0; i < TRIALS; i++) s[i] = new Plain();
        int[] r1 = new int[TRIALS], r2 = new int[TRIALS];
        race(i -> { s[i].x = 1; r1[i] = s[i].y; }, i -> { s[i].y = 1; r2[i] = s[i].x; });
        return bothZero(r1, r2);
    }

    static int xOnly() throws InterruptedException {
        XOnly[] s = new XOnly[TRIALS];
        for (int i = 0; i < TRIALS; i++) s[i] = new XOnly();
        int[] r1 = new int[TRIALS], r2 = new int[TRIALS];
        race(i -> { s[i].x = 1; r1[i] = s[i].y; }, i -> { s[i].y = 1; r2[i] = s[i].x; });
        return bothZero(r1, r2);
    }

    static int both() throws InterruptedException {
        Both[] s = new Both[TRIALS];
        for (int i = 0; i < TRIALS; i++) s[i] = new Both();
        int[] r1 = new int[TRIALS], r2 = new int[TRIALS];
        race(i -> { s[i].x = 1; r1[i] = s[i].y; }, i -> { s[i].y = 1; r2[i] = s[i].x; });
        return bothZero(r1, r2);
    }

    // Runs a(i) and b(i) for every trial on two threads, in lockstep batches so they overlap.
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
            while (other.get() < batch) Thread.onSpinWait();
            for (int i = batch * BATCH; i < (batch + 1) * BATCH; i++) side.accept(i);
        }
    }

    static int bothZero(int[] r1, int[] r2) {
        int n = 0;
        for (int i = 0; i < r1.length; i++) if (r1[i] == 0 && r2[i] == 0) n++;
        return n;
    }
}
