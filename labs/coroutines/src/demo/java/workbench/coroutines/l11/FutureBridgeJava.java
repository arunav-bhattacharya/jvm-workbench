// Java equivalent of FutureBridge.kt, from the Java side: plain Java calling the Kotlin
// SoupKitchen through its future {} method. No Continuation, no runBlocking.
package workbench.coroutines.l11;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

public class FutureBridgeJava {
    public static void main(String[] args) throws Exception {
        try (SoupKitchen kitchen = new SoupKitchen()) {
            System.out.println("1. compose two Kotlin calls like any futures:");
            CompletableFuture<Integer> bowls = kitchen.cookAsync("leek")
                .thenCombine(kitchen.cookAsync("tomato"), Integer::sum);
            System.out.println("  bowls in total: " + bowls.get(2, TimeUnit.SECONDS));

            System.out.println("2. a Java timeout cancels the Kotlin coroutine:");
            CompletableFuture<Integer> slow = kitchen.cookAsync("onion")
                .orTimeout(50, TimeUnit.MILLISECONDS);   // fails the future after 50 ms
            try { slow.join(); } catch (Exception e) { System.out.println("  java caller got: " + e.getCause()); }
            Thread.sleep(50);

            System.out.println("3. cancel(true) on the future the kitchen returned:");
            CompletableFuture<Integer> cancelled = kitchen.cookAsync("pea");
            Thread.sleep(50);
            cancelled.cancel(true);
            Thread.sleep(50);
            System.out.println("  future cancelled: " + cancelled.isCancelled());
        }
    }
}
