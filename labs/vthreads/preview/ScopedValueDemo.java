// JDK 25 or later. Scoped values are final in JDK 25 (JEP 506), so no flag is needed. From labs/vthreads:
//     java preview/ScopedValueDemo.java
// Not part of the Gradle build, because the labs compile for JDK 21, where ScopedValue is a preview API.

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class ScopedValueDemo {
    static final ThreadLocal<String> TENANT_TL = new ThreadLocal<>();
    static final ScopedValue<String> TENANT = ScopedValue.newInstance();

    // deep in the call chain: reads the context, never sets it
    static String ledgerLookup() {
        return "ThreadLocal=" + TENANT_TL.get() + ", ScopedValue=" + TENANT.orElse("unbound");
    }

    public static void main(String[] args) throws Exception {
        // 1. a ThreadLocal set on a pooled thread and never removed
        try (ExecutorService pool = Executors.newFixedThreadPool(1)) {
            pool.submit(() -> {
                TENANT_TL.set("bank-a");                        // forgot TENANT_TL.remove()
                return ledgerLookup();
            }).get();
            System.out.println("1. next task, same pool thread: " + pool.submit(ScopedValueDemo::ledgerLookup).get());
        }

        // 2. a scoped value is bound for one call, and gone afterwards
        ScopedValue.where(TENANT, "bank-a").run(() -> System.out.println("2. inside run():   " + ledgerLookup()));
        System.out.println("   after run():    " + ledgerLookup());

        // 3. rebind for a nested call; the outer binding comes back when it returns
        ScopedValue.where(TENANT, "bank-a").run(() -> {
            ScopedValue.where(TENANT, "bank-b").run(() -> System.out.println("3. nested:         " + ledgerLookup()));
            System.out.println("   outer again:    " + ledgerLookup());
        });

        // 4. a thread you start yourself does not inherit the binding
        ScopedValue.where(TENANT, "bank-a").run(() -> {
            Thread child = Thread.ofVirtual().start(() -> System.out.println("4. plain thread:   " + ledgerLookup()));
            try {
                child.join();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });
    }
}
