package workbench.ledger.l03.demo;

import java.util.concurrent.CompletionService;
import java.util.concurrent.ExecutorCompletionService;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/** One transfer, two checks. The limits check says no at 10 ms. When does the request get its answer? */
public class FailFastDemoJava {
    static long t0;

    static long ms() {
        return (System.nanoTime() - t0) / 1_000_000;
    }

    // the slow check: answers after 500 ms, unless it is interrupted first
    static boolean fraudCheck() throws InterruptedException {
        try {
            Thread.sleep(500);
            System.out.printf("  %4d ms  fraud check answered%n", ms());
            return true;
        } catch (InterruptedException e) {
            System.out.printf("  %4d ms  fraud check interrupted%n", ms());
            throw e;
        }
    }

    // the fast check: says no after 10 ms
    static boolean limitsCheck() throws InterruptedException {
        Thread.sleep(10);
        return false;
    }

    public static void main(String[] args) throws Exception {
        System.out.println("in order: get() the fraud check, then the limits check");
        t0 = System.nanoTime();
        try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
            Future<Boolean> fraud = perTask.submit(FailFastDemoJava::fraudCheck);
            Future<Boolean> limits = perTask.submit(FailFastDemoJava::limitsCheck);
            String verdict = fraud.get() && limits.get() ? "approved" : "declined";
            System.out.printf("  %4d ms  verdict: %s%n", ms(), verdict);
        }

        System.out.println("fail fast: take results as they finish, stop the rest at the first no");
        t0 = System.nanoTime();
        ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor();
        try {
            CompletionService<Boolean> done = new ExecutorCompletionService<>(perTask);
            done.submit(FailFastDemoJava::fraudCheck);
            done.submit(FailFastDemoJava::limitsCheck);
            String verdict = "approved";
            for (int i = 0; i < 2; i++) {
                if (!done.take().get()) { verdict = "declined"; break; }   // completion order, not submit order
            }
            System.out.printf("  %4d ms  verdict: %s%n", ms(), verdict);
        } finally {
            perTask.shutdownNow();                     // interrupt the check nobody needs any more
            perTask.close();                           // and wait until its thread has ended
        }
    }
}
