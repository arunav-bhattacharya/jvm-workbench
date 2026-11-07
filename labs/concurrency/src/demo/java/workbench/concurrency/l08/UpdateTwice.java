package workbench.concurrency.l08;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.LongAdder;

/** updateAndGet retries your function when it loses a race. Count how often the function really runs. */
public class UpdateTwice {
    public static void main(String[] args) throws InterruptedException {
        AtomicLong balance = new AtomicLong();
        LongAdder calls = new LongAdder();
        CountDownLatch go = new CountDownLatch(1);
        Runnable deposits = () -> {
            try { go.await(); } catch (InterruptedException e) { return; }
            for (int i = 0; i < 250_000; i++) {
                balance.updateAndGet(b -> {
                    calls.increment();          // a side effect: imagine this sent a notification
                    return b + 1;
                });
            }
        };
        Thread[] ts = {new Thread(deposits), new Thread(deposits), new Thread(deposits), new Thread(deposits)};
        for (Thread t : ts) t.start();
        go.countDown();                         // all four start together
        for (Thread t : ts) t.join();
        System.out.printf("updates: %,d   times the function ran: %,d%n", balance.get(), calls.sum());
    }
}
