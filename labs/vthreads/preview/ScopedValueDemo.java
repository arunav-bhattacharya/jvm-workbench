// JDK 25 or later. Scoped values are final in JDK 25 (JEP 506), so no flag is needed. From labs/:
//     java vthreads/preview/ScopedValueDemo.java
// Not part of the Gradle build, because the labs compile for JDK 21, where ScopedValue is a preview API.

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class ScopedValueDemo {
    static final ThreadLocal<String> CUSTOMER_TL = new ThreadLocal<>();
    static final ScopedValue<String> CUSTOMER = ScopedValue.newInstance();

    // deep in the call chain: reads the context, never sets it
    static String receiptLine() {
        return "ThreadLocal=" + CUSTOMER_TL.get() + ", ScopedValue=" + CUSTOMER.orElse("unbound");
    }

    public static void main(String[] args) throws Exception {
        // 1. a ThreadLocal set on a pooled thread and never removed
        try (ExecutorService pool = Executors.newFixedThreadPool(1)) {
            pool.submit(() -> {
                CUSTOMER_TL.set("ann");                         // forgot CUSTOMER_TL.remove()
                return receiptLine();
            }).get();
            System.out.println("1. next task, same pool thread: " + pool.submit(ScopedValueDemo::receiptLine).get());
        }

        // 2. a scoped value is bound for one call, and gone afterwards
        ScopedValue.where(CUSTOMER, "ann").run(() -> System.out.println("2. inside run():   " + receiptLine()));
        System.out.println("   after run():    " + receiptLine());

        // 3. rebind for a nested call; the outer binding comes back when it returns
        ScopedValue.where(CUSTOMER, "ann").run(() -> {
            ScopedValue.where(CUSTOMER, "ben").run(() -> System.out.println("3. nested:         " + receiptLine()));
            System.out.println("   outer again:    " + receiptLine());
        });

        // 4. a thread you start yourself does not inherit the binding
        ScopedValue.where(CUSTOMER, "ann").run(() -> {
            Thread child = Thread.ofVirtual().start(() -> System.out.println("4. plain thread:   " + receiptLine()));
            try {
                child.join();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });
    }
}
