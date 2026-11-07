package workbench.memory.l03;

import workbench.memory.Jvm;

import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

/** 1,000 objects with a finalize() method, in two child JVMs: default, and --finalization=disabled. */
public class FinalizerDemo {
    static final AtomicInteger finalized = new AtomicInteger();

    static class LegacyHandle {
        @Override
        @SuppressWarnings({"removal", "deprecation"})
        protected void finalize() {                                // deprecated for removal since JDK 18
            finalized.incrementAndGet();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        if (args.length == 0) {
            System.out.println("== default flags");
            Jvm.run(List.of(), FinalizerDemo.class.getName(), "run");
            System.out.println("== --finalization=disabled");
            Jvm.run(List.of("--finalization=disabled"), FinalizerDemo.class.getName(), "run");
            return;
        }
        for (int i = 0; i < 1_000; i++) new LegacyHandle();
        for (int i = 0; i < 20; i++) { System.gc(); Thread.sleep(20); }
        System.out.println("finalized " + finalized.get() + " of 1000");
    }
}
