package workbench.concurrency.l04;

/** Two unrelated classes each lock on the string "lock". They are the same object. */
public class SharedLiteralLock {
    static class TokenCache {
        void refresh() {
            synchronized ("lock") {                  // looks private. It isn't.
                sleep(1_000);                        // a slow refresh
            }
        }
    }

    static class Metrics {
        void record() {
            synchronized ("lock") {                  // a different class, a different "lock"?
                System.out.println("metrics: recorded");
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Thread refresher = new Thread(() -> new TokenCache().refresh(), "token-refresh");
        Thread metrics = new Thread(() -> new Metrics().record(), "metrics");
        refresher.start();
        Thread.sleep(100);                           // let the refresher take the lock first
        long t0 = System.nanoTime();
        metrics.start();
        Thread.sleep(200);
        System.out.println("metrics thread state after 200 ms: " + metrics.getState());
        metrics.join();
        System.out.printf("metrics waited about %d ms for a lock it never shared on purpose%n",
                (System.nanoTime() - t0) / 1_000_000);
        refresher.join();
    }

    static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }
}
