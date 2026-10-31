package workbench.concurrency.l04;

/** Eight threads authorize payments. Each call to the issuer takes 40 ms. Where should the lock go? */
public class SlowCallUnderLock {
    static final Object lock = new Object();
    static long approvedCents;

    public static void main(String[] args) throws InterruptedException {
        System.out.printf("issuer call inside the lock:  %,5d ms%n", run(true));
        System.out.printf("issuer call outside the lock: %,5d ms%n", run(false));
    }

    static long run(boolean callInsideLock) throws InterruptedException {
        approvedCents = 0;
        Thread[] threads = new Thread[8];
        long t0 = System.nanoTime();
        for (int i = 0; i < threads.length; i++) {
            threads[i] = new Thread(() -> {
                for (int p = 0; p < 5; p++) {
                    if (callInsideLock) {
                        synchronized (lock) {
                            boolean ok = callIssuer();          // 40 ms while every other thread waits
                            if (ok) approvedCents += 1_999;
                        }
                    } else {
                        boolean ok = callIssuer();              // slow work with no lock held
                        synchronized (lock) {                   // lock only the shared update
                            if (ok) approvedCents += 1_999;
                        }
                    }
                }
            });
            threads[i].start();
        }
        for (Thread t : threads) t.join();
        if (approvedCents != 40 * 1_999) throw new AssertionError("lost an update: " + approvedCents);
        return (System.nanoTime() - t0) / 1_000_000;
    }

    static boolean callIssuer() {
        try { Thread.sleep(40); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        return true;
    }
}
