package workbench.vthreads.l05;

import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/**
 * A checkout asks two services at the same time: the bank, which takes 2 s on a bad day,
 * and the stock service, which says "sold out" after 100 ms. Once the stock check has failed,
 * the bank's answer is useless. Watch what happens to the bank call anyway.
 */
public class LeakDemo {
    static volatile long t0;

    static void log(String what) {
        System.out.printf("%,7d ms  %s%n", (System.nanoTime() - t0) / 1_000_000, what);
    }

    static String bank() throws InterruptedException {
        try {
            Thread.sleep(2_000);                                  // the bank, on a bad day
            log("bank: answered, but nobody needs the answer");
            return "approved";
        } catch (InterruptedException e) {
            log("bank: interrupted, stopped early");
            throw e;
        }
    }

    static String stock() throws InterruptedException {
        Thread.sleep(100);
        throw new IllegalStateException("stock service: sold out");
    }

    // A: an executor per checkout, in try-with-resources
    static String checkoutA() throws Exception {
        try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
            Future<String> bank = perTask.submit(LeakDemo::bank);
            Future<String> stock = perTask.submit(LeakDemo::stock);
            return stock.get() + " " + bank.get();                // throws at 100 ms...
        }                                                         // ...but close() waits for the bank
    }

    static final ExecutorService SHARED = Executors.newVirtualThreadPerTaskExecutor();

    // B: one long-lived executor for the whole shop
    static String checkoutB() throws Exception {
        Future<String> bank = SHARED.submit(LeakDemo::bank);
        Future<String> stock = SHARED.submit(LeakDemo::stock);
        return stock.get() + " " + bank.get();                    // throws at 100 ms, and returns
    }

    public static void main(String[] args) throws Exception {
        System.out.println("A: an executor per checkout, closed by try-with-resources");
        t0 = System.nanoTime();
        try {
            checkoutA();
        } catch (ExecutionException e) {
            log("checkout failed: " + e.getCause().getMessage());
        }

        System.out.println("B: one shared executor");
        t0 = System.nanoTime();
        try {
            checkoutB();
        } catch (ExecutionException e) {
            log("checkout failed: " + e.getCause().getMessage());
        }
        Thread.sleep(2_500);                                      // stay alive to see what B left behind
        SHARED.close();
    }
}
