package workbench.memory.l02;

import workbench.memory.Jvm;

import java.util.List;

/**
 * Allocates 2,000,000 small arrays in a child JVM that logs a TLAB summary at every GC.
 * Each "refills" count is how often a thread went back to eden for a fresh buffer.
 */
public class TlabDemo {
    static volatile Object sink;

    public static void main(String[] args) {
        if (args.length == 0) {
            for (String line : Jvm.lines(List.of("-Xmx256m", "-Xlog:gc,gc+tlab=debug"), TlabDemo.class.getName(), "allocate")) {
                System.out.println(line.replaceAll("\\s+", " "));
            }
            return;
        }
        for (int i = 0; i < 2_000_000; i++) sink = new byte[24];   // 16-byte header + 24 bytes = 40 bytes each
        System.out.println("allocated 2,000,000 arrays of 40 bytes: 80,000,000 bytes");
    }
}
