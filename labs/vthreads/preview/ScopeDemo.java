// JDK 25 only. StructuredTaskScope is a preview API in JDK 25 (JEP 505). From labs/:
//     java --enable-preview --source 25 vthreads/preview/ScopeDemo.java
// The quote handler from LeakDemo, written with a scope. Not part of the Gradle build.

import java.time.Duration;
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.StructuredTaskScope.Joiner;   // for the Try it
import java.util.concurrent.StructuredTaskScope.Subtask;

public class ScopeDemo {
    static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();
    static final long T0 = System.nanoTime();

    static void log(String what) {
        System.out.printf("%,7d ms  [%s] %s%n", (System.nanoTime() - T0) / 1_000_000, REQUEST_ID.orElse("-"), what);
    }

    static String customer() throws InterruptedException {
        try {
            Thread.sleep(2_000);                                // the slow CRM call
            log("customer: call finished");
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

    static String quote() throws InterruptedException {
        try (var scope = StructuredTaskScope.open()) {           // default joiner: fail on the first failure
            Subtask<String> customer = scope.fork(ScopeDemo::customer);
            Subtask<String> limit = scope.fork(ScopeDemo::limit);
            scope.join();                                       // throws FailedException at about 100 ms
            return limit.get() + " " + customer.get();
        }                                                       // close(): every subtask has ended
    }

    static void handle() {
        try {
            log("quote: " + quote());
        } catch (StructuredTaskScope.FailedException e) {
            log("request failed: " + e.getCause().getMessage());
        } catch (StructuredTaskScope.TimeoutException e) {
            log("request timed out");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public static void main(String[] args) {
        ScopedValue.where(REQUEST_ID, "req-42").run(ScopeDemo::handle);   // subtasks see req-42 too
        log("done: the binding has ended, and no subtask is still running");
    }
}
