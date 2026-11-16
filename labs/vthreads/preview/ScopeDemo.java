// JDK 25 only. StructuredTaskScope is a preview API in JDK 25 (JEP 505). From labs/:
//     java --enable-preview --source 25 vthreads/preview/ScopeDemo.java
// The checkout from LeakDemo, written with a scope. Not part of the Gradle build.

import java.time.Duration;
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.StructuredTaskScope.Joiner;   // for the Try it
import java.util.concurrent.StructuredTaskScope.Subtask;

public class ScopeDemo {
    static final ScopedValue<String> ORDER_ID = ScopedValue.newInstance();
    static final long T0 = System.nanoTime();

    static void log(String what) {
        System.out.printf("%,7d ms  [%s] %s%n", (System.nanoTime() - T0) / 1_000_000, ORDER_ID.orElse("-"), what);
    }

    static String bank() throws InterruptedException {
        try {
            Thread.sleep(2_000);                                // the bank, on a bad day
            log("bank: answered");
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

    static String checkout() throws InterruptedException {
        try (var scope = StructuredTaskScope.open()) {           // default joiner: fail on the first failure
            Subtask<String> bank = scope.fork(ScopeDemo::bank);
            Subtask<String> stock = scope.fork(ScopeDemo::stock);
            scope.join();                                       // throws FailedException at about 100 ms
            return stock.get() + " " + bank.get();
        }                                                       // close(): every subtask has ended
    }

    static void handle() {
        try {
            log("checkout: " + checkout());
        } catch (StructuredTaskScope.FailedException e) {
            log("checkout failed: " + e.getCause().getMessage());
        } catch (StructuredTaskScope.TimeoutException e) {
            log("checkout timed out");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public static void main(String[] args) {
        ScopedValue.where(ORDER_ID, "order-42").run(ScopeDemo::handle);   // subtasks see order-42 too
        log("done: the binding has ended, and no subtask is still running");
    }
}
