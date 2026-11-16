package workbench.concurrency.l02;

import java.time.Duration;

/** join(timeout) gives up waiting; join() waits for the end and makes the result visible. */
public class JoinWithTimeout {
    static long priceCents;                // plain field: join() is what makes the write visible

    public static void main(String[] args) throws InterruptedException {
        Thread fetch = new Thread(() -> {
            sleepQuietly(500);             // stands in for a slow web service that answers in 500 ms
            priceCents = 10_842;
        }, "price-fetch");
        fetch.start();

        boolean ended = fetch.join(Duration.ofMillis(100));   // JDK 19+: returns whether it ended
        System.out.println("after join(100 ms): ended=" + ended + ", alive=" + fetch.isAlive() + ", price=" + priceCents);

        fetch.join();                      // no timeout: wait for the end
        System.out.println("after join():       alive=" + fetch.isAlive() + ", price=" + priceCents);
    }

    static void sleepQuietly(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }
}
