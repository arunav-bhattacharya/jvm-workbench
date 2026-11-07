package workbench.concurrency.l10;

import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/** Three workers, three rounds, one barrier that resets itself. Then a round where one worker never shows up. */
public class BarrierDemo {
    public static void main(String[] args) throws InterruptedException {
        long[] shares = new long[3];
        CyclicBarrier endOfDay = new CyclicBarrier(3, () ->       // runs once per round, before anyone moves on
                System.out.printf("  day closed by %s: exposure %,d%n",
                        Thread.currentThread().getName(), shares[0] + shares[1] + shares[2]));

        Thread[] workers = new Thread[3];
        for (int w = 0; w < 3; w++) {
            int me = w;
            workers[w] = new Thread(() -> {
                try {
                    for (int day = 1; day <= 3; day++) {
                        Thread.sleep(50L * (me + 1));                  // workers finish at different times
                        shares[me] = 1_000L * day * (me + 1);
                        endOfDay.await();                              // wait for the other two
                    }
                    // day 4: worker 2 never arrives, the others give up after 300 ms
                    if (me == 2) return;
                    endOfDay.await(300, TimeUnit.MILLISECONDS);
                } catch (TimeoutException e) {
                    System.out.println("  " + Thread.currentThread().getName() + ": TimeoutException, barrier now broken");
                } catch (BrokenBarrierException e) {
                    System.out.println("  " + Thread.currentThread().getName() + ": BrokenBarrierException");
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }, "worker-" + w);
            workers[w].start();
        }
        for (Thread t : workers) t.join();
        System.out.println("broken: " + endOfDay.isBroken());
    }
}
