package workbench.executors.l07;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** The steak burns at the grill. Which steps still run? Pass "early" to recover right after the grill. */
public class ErrorPathDemo {
    static String grill() {
        throw new IllegalStateException("the steak burned");
    }

    static <T> T step(String what, T value) {
        System.out.println(what);
        return value;
    }

    public static void main(String[] args) {
        boolean early = args.length > 0 && args[0].equals("early");
        try (ExecutorService kitchen = Executors.newFixedThreadPool(1, Thread.ofPlatform().name("cook-", 1).factory())) {
            CompletableFuture<String> steak = CompletableFuture.supplyAsync(ErrorPathDemo::grill, kitchen);
            if (early) {
                steak = steak.exceptionally(ex -> {                  // recover the steak itself
                    System.out.println("exceptionally sees: " + ex);
                    return "the spare steak";                        // kept warm for nights like this
                });
            }
            CompletableFuture<String> result = steak
                    .thenApply(s -> step("1. pour the sauce on " + s, s + " with pepper sauce"))
                    .thenApply(s -> step("2. plate " + s, "a plate of " + s))
                    .thenApply(s -> step("3. carry it to table 4", "table 4 got " + s))
                    .whenComplete((v, ex) -> System.out.println("whenComplete sees: " + (ex == null ? v : ex)));
            if (!early) {
                result = result.exceptionally(ex -> {                // recover at the pass instead
                    System.out.println("exceptionally sees: " + ex);
                    return "table 4 got an apology and the menu";
                });
            }
            System.out.println("result: " + result.join());
        }
    }
}
