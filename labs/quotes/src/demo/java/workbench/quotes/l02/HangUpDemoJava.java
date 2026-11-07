// Java equivalent with CompletableFuture: cancel() completes the future, but the calls behind it run on
package workbench.quotes.l02;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** A request built from three supplyAsync calls. The client hangs up after 120 ms. */
public class HangUpDemoJava {
    static final long t0 = System.nanoTime();

    static long ms() {
        return (System.nanoTime() - t0) / 1_000_000;
    }

    static String call(String name, long latency) {
        try {
            Thread.sleep(latency);
            System.out.println("  " + name + " answered at " + ms() + " ms, and nobody is listening");
            return name;
        } catch (InterruptedException e) {
            System.out.println("  " + name + " interrupted at " + ms() + " ms");
            return null;
        }
    }

    public static void main(String[] args) throws Exception {
        try (ExecutorService pool = Executors.newVirtualThreadPerTaskExecutor()) {
            List<CompletableFuture<String>> calls = List.of(
                    CompletableFuture.supplyAsync(() -> call("northbank", 300), pool),
                    CompletableFuture.supplyAsync(() -> call("eastgate", 400), pool),
                    CompletableFuture.supplyAsync(() -> call("fjord", 500), pool));
            CompletableFuture<List<String>> request = CompletableFuture.allOf(calls.toArray(CompletableFuture[]::new))
                    .thenApply(v -> calls.stream().map(CompletableFuture::join).toList());
            Thread.sleep(120);
            System.out.println("client hangs up at " + ms() + " ms: the handler calls request.cancel(true)");
            request.cancel(true);
            System.out.println("request cancelled: " + request.isCancelled() + ", calls cancelled: "
                    + calls.stream().filter(CompletableFuture::isCancelled).count() + " of 3");
        }   // close() waits for the three calls, which finish anyway
        System.out.println("at " + ms() + " ms: all three calls have finished");
    }
}
