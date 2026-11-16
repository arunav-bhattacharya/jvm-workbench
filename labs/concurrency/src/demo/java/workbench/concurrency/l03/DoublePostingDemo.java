package workbench.concurrency.l03;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * The same 1,000 payments reach eight teller threads, as if every payment arrived eight times.
 * Each teller records a payment only if nobody has recorded it yet: check-then-act on a ConcurrentHashMap.
 */
public class DoublePostingDemo {
    public static void main(String[] args) throws InterruptedException {
        Map<Integer, String> recordedBy = new ConcurrentHashMap<>();   // payment id -> the teller that recorded it
        AtomicInteger recorded = new AtomicInteger();
        Thread[] tellers = new Thread[8];
        for (int c = 0; c < tellers.length; c++) {
            String me = "teller-" + c;
            tellers[c] = new Thread(() -> {
                for (int payment = 0; payment < 1_000; payment++) {
                    if (!recordedBy.containsKey(payment)) {                     // check
                        for (int i = 0; i < 300; i++) Thread.onSpinWait();     // a slow step: is the payment genuine?
                        recordedBy.put(payment, me);                           // act
                        recorded.incrementAndGet();                            // the money moves
                    }
                }
            }, me);
        }
        for (Thread t : tellers) t.start();
        for (Thread t : tellers) t.join();
        System.out.printf("payments: 1,000  times recorded: %,d  duplicates: %,d%n",
                recorded.get(), recorded.get() - 1_000);
    }
}
