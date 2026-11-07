package workbench.vthreads.l05;

import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/**
 * A quote handler fans out two calls: a slow CRM lookup (2 s) and a credit-limit check
 * that fails after 100 ms. Watch what happens to the slow call once the request has failed.
 */
public class LeakDemo {
    static volatile long t0;

    static void log(String what) {
        System.out.printf("%,7d ms  %s%n", (System.nanoTime() - t0) / 1_000_000, what);
    }

    static String customer() throws InterruptedException {
        try {
            Thread.sleep(2_000);                                  // the slow CRM call
            log("customer: call finished, nobody needs the result");
            return "ACME Ltd";
        } catch (InterruptedException e) {
            log("customer: interrupted, stopped early");
            throw e;
        }
    }

    static String limit() throws InterruptedException {
        Thread.sleep(100);
        throw new IllegalStateException("credit limit service: 503");
    }

    // A: an executor per request, in try-with-resources
    static String quoteA() throws Exception {
        try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
            Future<String> customer = perTask.submit(LeakDemo::customer);
            Future<String> limit = perTask.submit(LeakDemo::limit);
            return limit.get() + " " + customer.get();            // throws at 100 ms...
        }                                                         // ...but close() waits for the CRM call
    }

    static final ExecutorService SHARED = Executors.newVirtualThreadPerTaskExecutor();

    // B: one long-lived executor for the whole service
    static String quoteB() throws Exception {
        Future<String> customer = SHARED.submit(LeakDemo::customer);
        Future<String> limit = SHARED.submit(LeakDemo::limit);
        return limit.get() + " " + customer.get();                // throws at 100 ms, and returns
    }

    public static void main(String[] args) throws Exception {
        System.out.println("A: executor per request, closed by try-with-resources");
        t0 = System.nanoTime();
        try {
            quoteA();
        } catch (ExecutionException e) {
            log("request failed: " + e.getCause().getMessage());
        }

        System.out.println("B: one shared executor");
        t0 = System.nanoTime();
        try {
            quoteB();
        } catch (ExecutionException e) {
            log("request failed: " + e.getCause().getMessage());
        }
        Thread.sleep(2_500);                                      // stay alive to see what B left behind
        SHARED.close();
    }
}
