package workbench.jmm.l01;

import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.IntConsumer;

/**
 * The store-buffering test. Thread A runs {@code x = 1; r1 = y;} and thread B runs {@code y = 1; r2 = x;}.
 * If the four lines ran in any order that keeps each thread's two lines in program order,
 * at least one thread would read a 1. Count the trials where both threads read 0.
 */
public class ReorderDemo {
    static final class Plain { int x, y; }
    static final class Volatile { volatile int x, y; }

    static final int TRIALS = 1 << 19;
    static final int BATCH = 32;

    public static void main(String[] args) throws InterruptedException {
        for (int run = 1; run <= 3; run++) {
            System.out.printf("run %d: both read 0 in %,7d trials with plain fields, %,d with volatile fields (of %,d)%n",
                    run, plain(), withVolatile(), TRIALS);
        }
    }

    static int plain() throws InterruptedException {
        Plain[] s = new Plain[TRIALS];
        for (int i = 0; i < TRIALS; i++) s[i] = new Plain();
        int[] r1 = new int[TRIALS], r2 = new int[TRIALS];
        race(i -> { s[i].x = 1; r1[i] = s[i].y; },
             i -> { s[i].y = 1; r2[i] = s[i].x; });
        return bothZero(r1, r2);
    }

    static int withVolatile() throws InterruptedException {
        Volatile[] s = new Volatile[TRIALS];
        for (int i = 0; i < TRIALS; i++) s[i] = new Volatile();
        int[] r1 = new int[TRIALS], r2 = new int[TRIALS];
        race(i -> { s[i].x = 1; r1[i] = s[i].y; },
             i -> { s[i].y = 1; r2[i] = s[i].x; });
        return bothZero(r1, r2);
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
