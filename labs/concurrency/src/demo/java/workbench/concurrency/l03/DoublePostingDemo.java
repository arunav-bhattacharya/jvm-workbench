package workbench.concurrency.l03;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * A replay hands the same 1,000 payment events to eight consumer threads. Each consumer posts a
 * payment to the ledger only if no one has posted it yet: check-then-act on a ConcurrentHashMap.
 */
public class DoublePostingDemo {
    public static void main(String[] args) throws InterruptedException {
        Map<Integer, String> postedBy = new ConcurrentHashMap<>();   // payment id -> the consumer that posted it
        AtomicInteger postings = new AtomicInteger();
        Thread[] consumers = new Thread[8];
        for (int c = 0; c < consumers.length; c++) {
            String me = "consumer-" + c;
            consumers[c] = new Thread(() -> {
                for (int payment = 0; payment < 1_000; payment++) {
                    if (!postedBy.containsKey(payment)) {                       // check
                        for (int i = 0; i < 300; i++) Thread.onSpinWait();     // a slow step: the fraud check
                        postedBy.put(payment, me);                             // act
                        postings.incrementAndGet();                            // the money moves
                    }
                }
            }, me);
        }
        for (Thread t : consumers) t.start();
        for (Thread t : consumers) t.join();
        System.out.printf("payments: 1,000  postings: %,d  duplicate postings: %,d%n",
                postings.get(), postings.get() - 1_000);
    }
}
