package workbench.concurrency.l04;

/** Eight threads make transfers. Each one first asks a fraud-check service, which takes 40 ms. Where should the lock go? */
public class SlowCallUnderLock {
    static final Object lock = new Object();
    static long movedCents;

    public static void main(String[] args) throws InterruptedException {
        System.out.printf("fraud check inside the lock:  %,5d ms%n", run(true));
        System.out.printf("fraud check outside the lock: %,5d ms%n", run(false));
    }

    static long run(boolean checkInsideLock) throws InterruptedException {
        movedCents = 0;
        Thread[] threads = new Thread[8];
        long t0 = System.nanoTime();
        for (int i = 0; i < threads.length; i++) {
            threads[i] = new Thread(() -> {
                for (int p = 0; p < 5; p++) {
                    if (checkInsideLock) {
                        synchronized (lock) {
                            boolean ok = checkForFraud();       // 40 ms while every other thread waits
                            if (ok) movedCents += 1_999;
                        }
                    } else {
                        boolean ok = checkForFraud();           // slow work with no lock held
                        synchronized (lock) {                   // lock only the shared update
                            if (ok) movedCents += 1_999;
                        }
                    }
                }
            });
            threads[i].start();
        }
        for (Thread t : threads) t.join();
        if (movedCents != 40 * 1_999) throw new AssertionError("lost an update: " + movedCents);
        return (System.nanoTime() - t0) / 1_000_000;
    }

    /** Stands in for a call to a fraud-check web service: 40 ms, and the answer is "looks fine". */
    static boolean checkForFraud() {
        try { Thread.sleep(40); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        return true;
    }
}
