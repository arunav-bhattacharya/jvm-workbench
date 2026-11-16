package workbench.concurrency.l10;

import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/**
 * Three threads add up the shop's three tills, day by day, and meet at one barrier that resets itself.
 * Then a day when one till never reports.
 */
public class BarrierDemo {
    public static void main(String[] args) throws InterruptedException {
        long[] sales = new long[3];                                // one slot per till, written by its own thread
        int[] day = {0};
        CyclicBarrier endOfDay = new CyclicBarrier(3, () ->        // runs once per day, before anyone moves on
                System.out.printf("  day %d closed by %s: sales %,d%n",
                        ++day[0], Thread.currentThread().getName(), sales[0] + sales[1] + sales[2]));

        Thread[] tills = new Thread[3];
        for (int w = 0; w < 3; w++) {
            int me = w;
            tills[w] = new Thread(() -> {
                try {
                    for (int d = 1; d <= 3; d++) {
                        Thread.sleep(50L * (me + 1));                  // the tills finish at different times
                        sales[me] = 1_000L * d * (me + 1);
                        endOfDay.await();                              // wait for the other two
                    }
                    // day 4: till 2 never reports, the others give up after 300 ms
                    if (me == 2) return;
                    endOfDay.await(300, TimeUnit.MILLISECONDS);
                } catch (TimeoutException e) {
                    System.out.println("  " + Thread.currentThread().getName() + ": TimeoutException, barrier now broken");
                } catch (BrokenBarrierException e) {
                    System.out.println("  " + Thread.currentThread().getName() + ": BrokenBarrierException");
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }, "till-" + w);
            tills[w].start();
        }
        for (Thread t : tills) t.join();
        System.out.println("broken: " + endOfDay.isBroken());
    }
}
