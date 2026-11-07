package workbench.memory.l03;

import workbench.memory.Jvm;

import java.lang.ref.SoftReference;
import java.util.List;

/** A 40 MB soft-referenced "rate table" in a 64 MB heap, then another 40 MB allocation. Runs in a child JVM. */
public class SoftCacheDemo {
    public static void main(String[] args) {
        if (args.length == 0) {
            Jvm.run(List.of("-Xmx64m", "-Xlog:gc"), SoftCacheDemo.class.getName(), "run");
            return;
        }
        SoftReference<byte[]> rates = new SoftReference<>(new byte[40 << 20]);
        System.out.println("rate table cached: " + (rates.get() != null));
        byte[] report = new byte[40 << 20];                // only fits if the GC clears the soft reference
        System.out.println("after a 40 MB report: rate table cached: " + (rates.get() != null) + ", report " + report.length + " bytes");
    }
}
