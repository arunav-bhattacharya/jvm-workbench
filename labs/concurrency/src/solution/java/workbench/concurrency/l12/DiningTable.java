package workbench.concurrency.l12;

import java.util.concurrent.locks.ReentrantLock;

public class DiningTable {
    private final ReentrantLock[] forks;

    public DiningTable(int seats) {
        if (seats < 2) throw new IllegalArgumentException("need at least 2 seats, was " + seats);
        forks = new ReentrantLock[seats];
        for (int i = 0; i < seats; i++) forks[i] = new ReentrantLock();
    }

    public int seats() {
        return forks.length;
    }

    public void dine(int seat, int meals, Runnable eat) {
        int a = seat, b = (seat + 1) % forks.length;
        ReentrantLock first = forks[Math.min(a, b)];    // 1. lower-numbered fork first, for EVERY philosopher
        ReentrantLock second = forks[Math.max(a, b)];   //    the last one reaches right first: the cycle is gone
        for (int m = 0; m < meals; m++) {
            first.lock();
            try {
                reachForTheOtherFork();
                second.lock();
                try {
                    eat.run();                          // 2. both forks held
                } finally {
                    second.unlock();
                }
            } finally {
                first.unlock();
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
