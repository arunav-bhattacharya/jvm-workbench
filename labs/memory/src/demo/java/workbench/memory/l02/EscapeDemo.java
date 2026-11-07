package workbench.memory.l02;

import com.sun.management.ThreadMXBean;
import workbench.memory.Jvm;

import java.lang.management.ManagementFactory;
import java.util.List;

/**
 * Sums a million short-lived Points per round and counts the bytes each round allocates.
 * The demo runs the experiment twice, in child JVMs: with escape analysis, and without it.
 */
public class EscapeDemo {
    record Point(long x, long y) {}                                // 12-byte header + 16 bytes of fields: 32 bytes

    static long sumPoints(int n) {
        long s = 0;
        for (int i = 0; i < n; i++) {
            Point p = new Point(i, i + 1);                         // p never leaves this method
            s += p.x() + p.y();
        }
        return s;
    }

    public static void main(String[] args) {
        if (args.length == 0) {
            System.out.println("== default flags: escape analysis on");
            Jvm.run(List.of(), EscapeDemo.class.getName(), "measure");
            System.out.println("== -XX:-DoEscapeAnalysis");
            Jvm.run(List.of("-XX:-DoEscapeAnalysis"), EscapeDemo.class.getName(), "measure");
            return;
        }
        ThreadMXBean threads = (ThreadMXBean) ManagementFactory.getThreadMXBean();
        long checksum = 0;
        for (int round = 0; round < 10; round++) {
            long before = threads.getCurrentThreadAllocatedBytes();
            checksum += sumPoints(1_000_000);
            long bytes = threads.getCurrentThreadAllocatedBytes() - before;
            System.out.printf("round %d: %,12d bytes%n", round, bytes);
        }
        System.out.println("checksum " + checksum);
    }
}
