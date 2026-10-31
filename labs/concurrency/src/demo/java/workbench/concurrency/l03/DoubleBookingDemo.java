package workbench.concurrency.l03;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/** Eight buyers race for the same 1,000 seats using check-then-act on a ConcurrentHashMap. */
public class DoubleBookingDemo {
    public static void main(String[] args) throws InterruptedException {
        Map<Integer, String> owners = new ConcurrentHashMap<>();
        AtomicInteger sold = new AtomicInteger();
        Thread[] buyers = new Thread[8];
        for (int b = 0; b < buyers.length; b++) {
            String me = "buyer-" + b;
            buyers[b] = new Thread(() -> {
                for (int seat = 0; seat < 1_000; seat++) {
                    if (!owners.containsKey(seat)) {                       // check
                        for (int i = 0; i < 300; i++) Thread.onSpinWait(); // a slow step
                        owners.put(seat, me);                              // act
                        sold.incrementAndGet();
                    }
                }
            });
        }
        for (Thread t : buyers) t.start();
        for (Thread t : buyers) t.join();
        System.out.printf("seats: 1,000  tickets sold: %,d  double-booked: %,d%n", sold.get(), sold.get() - 1_000);
    }
}
