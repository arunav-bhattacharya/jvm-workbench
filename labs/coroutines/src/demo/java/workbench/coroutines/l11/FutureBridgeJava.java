// Java equivalent of FutureBridge.kt, from the Java side: plain Java calling the Kotlin
// FraudFacade through its future {} methods. No Continuation, no runBlocking.
package workbench.coroutines.l11;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

public class FutureBridgeJava {
    public static void main(String[] args) throws Exception {
        try (FraudFacade facade = new FraudFacade()) {
            System.out.println("1. compose two Kotlin calls like any futures:");
            CompletableFuture<Integer> total = facade.scoreAsync("pay-1")
                .thenCombine(facade.scoreAsync("pay-22"), Integer::sum);
            System.out.println("  combined score: " + total.get(2, TimeUnit.SECONDS));

            System.out.println("2. a Java timeout cancels the Kotlin coroutine:");
            CompletableFuture<Integer> slow = facade.scoreAsync("pay-timeout")
                .orTimeout(50, TimeUnit.MILLISECONDS);   // fails the future after 50 ms
            try { slow.join(); } catch (Exception e) { System.out.println("  java caller got: " + e.getCause()); }
            Thread.sleep(50);

            System.out.println("3. cancel(true) on the future the facade returned:");
            CompletableFuture<Integer> cancelled = facade.scoreAsync("pay-cancel");
            Thread.sleep(50);
            cancelled.cancel(true);
            Thread.sleep(50);
            System.out.println("  future cancelled: " + cancelled.isCancelled());
        }
    }
}
