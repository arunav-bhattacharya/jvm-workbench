package workbench.concurrency.l12;

import java.util.concurrent.locks.ReentrantLock;

/**
 * Philosophers at a round table, one fork between each pair of neighbours. Philosopher {@code i}
 * needs fork {@code i} (left) and fork {@code (i + 1) % seats} (right) to eat.
 *
 * <p>This version takes the left fork, then the right one. If every philosopher picks up a left fork
 * at the same moment, each waits for a right fork that its neighbour holds, forever.
 * Fix {@link #dine} with a global lock order: always take the lower-numbered fork first.
 * Keep {@link #reachForTheOtherFork()} between the two forks; it only makes the deadlock likely.
 */
public class DiningTable {
    private final ReentrantLock[] forks;

    /** @throws IllegalArgumentException if {@code seats} is less than 2 */
    public DiningTable(int seats) {
        if (seats < 2) throw new IllegalArgumentException("need at least 2 seats, was " + seats);
        forks = new ReentrantLock[seats];
        for (int i = 0; i < seats; i++) forks[i] = new ReentrantLock();
    }

    public int seats() {
        return forks.length;
    }

    /** Philosopher {@code seat} eats {@code meals} times, running {@code eat} while holding both forks. */
    public void dine(int seat, int meals, Runnable eat) {
        ReentrantLock left = forks[seat];
        ReentrantLock right = forks[(seat + 1) % forks.length];
        for (int m = 0; m < meals; m++) {
            left.lock();
            try {
                reachForTheOtherFork();
                right.lock();
                try {
                    eat.run();
                } finally {
                    right.unlock();
                }
            } finally {
                left.unlock();
            }
        }
    }

    private static void reachForTheOtherFork() {
        try {
            Thread.sleep(1);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
