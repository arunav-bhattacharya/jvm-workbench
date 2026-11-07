package workbench.memory.l03;

import java.lang.management.ManagementFactory;
import java.lang.ref.Reference;
import java.lang.ref.ReferenceQueue;
import java.util.function.BooleanSupplier;

import com.sun.management.HotSpotDiagnosticMXBean;

/**
 * Bounded waits for the garbage collector. System.gc() is only a request, so these helpers ask
 * repeatedly and give up after a few seconds instead of hanging the build.
 */
final class GcWait {
    private GcWait() {}

    /** Requests GCs until {@code probe} shows up on {@code queue}. Returns false after about 2.5 seconds. */
    static boolean untilEnqueued(ReferenceQueue<?> queue, Reference<?> probe) throws InterruptedException {
        requireExplicitGc();
        for (int i = 0; i < 50; i++) {
            System.gc();
            Reference<?> r = queue.remove(50);
            if (r == probe) return true;
        }
        return false;
    }

    /** Requests GCs until {@code condition} holds. Returns false after about 2.5 seconds. */
    static boolean until(BooleanSupplier condition) throws InterruptedException {
        requireExplicitGc();
        for (int i = 0; i < 50 && !condition.getAsBoolean(); i++) {
            System.gc();
            Thread.sleep(50);
        }
        return condition.getAsBoolean();
    }

    private static void requireExplicitGc() {
        var hotspot = ManagementFactory.getPlatformMXBean(HotSpotDiagnosticMXBean.class);
        if (Boolean.parseBoolean(hotspot.getVMOption("DisableExplicitGC").getValue())) {
            throw new IllegalStateException("these tests need System.gc(): remove -XX:+DisableExplicitGC");
        }
    }
}
