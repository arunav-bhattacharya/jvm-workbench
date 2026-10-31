package workbench.executors.l04;

import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

/** Three FX-rate providers with different speeds: invokeAny takes the first, invokeAll waits with a deadline. */
public class InvokeAnyDemo {
    static Callable<String> provider(String name, long millis, boolean fails) {
        return () -> {
            try {
                Thread.sleep(millis);
            } catch (InterruptedException e) {
                System.out.println("  " + name + ": interrupted, cancelled");
                throw e;
            }
            if (fails) throw new IllegalStateException(name + " is down");
            return name + " EUR/USD 1.0842";
        };
    }

    public static void main(String[] args) throws Exception {
        List<Callable<String>> providers = List.of(
                provider("alpha", 300, false),
                provider("beta", 100, true),      // fastest, but fails
                provider("gamma", 200, false));
        try (ExecutorService pool = Executors.newFixedThreadPool(3)) {
            System.out.println("invokeAny -> " + pool.invokeAny(providers));
            Thread.sleep(50);

            System.out.println("invokeAll with a 250 ms deadline:");
            List<Future<String>> all = pool.invokeAll(providers, 250, TimeUnit.MILLISECONDS);
            for (Future<String> f : all) {
                System.out.println("  " + f.state() + switch (f.state()) {
                    case SUCCESS -> ": " + f.resultNow();
                    case FAILED -> ": " + f.exceptionNow().getMessage();
                    default -> "";
                });
            }
        }
    }
}
