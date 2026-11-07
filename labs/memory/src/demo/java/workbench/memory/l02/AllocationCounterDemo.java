package workbench.memory.l02;

import com.sun.management.ThreadMXBean;

import java.lang.management.ManagementFactory;

/** Counts the bytes a few small pieces of code allocate, twice each, using the JVM's per-thread counter. */
public class AllocationCounterDemo {
    static final ThreadMXBean THREADS = (ThreadMXBean) ManagementFactory.getThreadMXBean();
    static volatile Object sink;                                   // results escape here, so nothing is optimized away

    static long bytes(Runnable work) {
        long before = THREADS.getCurrentThreadAllocatedBytes();
        work.run();
        return THREADS.getCurrentThreadAllocatedBytes() - before;
    }

    static void show(String what, Runnable work) {
        long first = bytes(work);                                  // the first run also pays for one-time setup
        long second = bytes(work);
        System.out.printf("%-34s %,10d %,11d%n", what, first, second);
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.printf("%-34s %10s %11s%n", "bytes allocated by", "first run", "second run");
        show("new byte[1 MiB]", () -> sink = new byte[1 << 20]);
        show("1,000 x Long.valueOf(i % 128)", () -> { for (int i = 0; i < 1_000; i++) sink = Long.valueOf(i % 128); });
        show("1,000 x Long.valueOf(1_000 + i)", () -> { for (int i = 0; i < 1_000; i++) sink = Long.valueOf(1_000 + i); });
        show("1,000 x \"pay-\" + i", () -> { for (int i = 0; i < 1_000; i++) sink = "pay-" + i; });

        Thread.ofVirtual().start(() ->
                System.out.println("on a virtual thread the counter says " + THREADS.getCurrentThreadAllocatedBytes())).join();
    }
}
