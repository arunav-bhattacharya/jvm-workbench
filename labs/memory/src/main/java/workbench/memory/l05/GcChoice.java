package workbench.memory.l05;

import java.util.List;

/**
 * Three questions about collectors, answered from the JDK source and from the lesson's decision table.
 */
public final class GcChoice {
    private GcChoice() {}

    /**
     * The collector the JVM picks when you name none. On JDK 21 to 26 it picks G1 only on a
     * "server-class machine": at least 2 CPUs and at least 1,792 MB of memory (2 GB minus 256 MB), as the
     * JVM sees them inside a container. Otherwise it picks Serial. From JDK 27 it always picks G1.
     */
    public static Collector defaultCollector(int jdk, int cpus, long memoryMb) {
        throw new UnsupportedOperationException("TODO: the server-class rule for JDK 21 to 26, G1 always from 27");
    }

    /**
     * The command-line flags that select {@code collector} on {@code jdk}. Experimental options need
     * {@code -XX:+UnlockExperimentalVMOptions}, and it must come before them.
     * <ul>
     *   <li>SERIAL, PARALLEL, G1: {@code -XX:+UseSerialGC}, {@code -XX:+UseParallelGC}, {@code -XX:+UseG1GC}</li>
     *   <li>ZGC (generational): {@code -XX:+UseZGC}, plus {@code -XX:+ZGenerational} before JDK 23</li>
     *   <li>SHENANDOAH: {@code -XX:+UseShenandoahGC}</li>
     *   <li>SHENANDOAH_GENERATIONAL: {@code -XX:+UseShenandoahGC -XX:ShenandoahGCMode=generational};
     *       experimental on JDK 24, a product mode from JDK 25, not available before JDK 24
     *       (throw IllegalArgumentException)</li>
     *   <li>EPSILON: experimental on every JDK this course covers: {@code -XX:+UseEpsilonGC}</li>
     * </ul>
     */
    public static List<String> flagsFor(Collector collector, int jdk) {
        throw new UnsupportedOperationException("TODO: the flags per collector and JDK");
    }

    /**
     * The lesson's decision table, first matching row wins:
     * <ol>
     *   <li>an allocation-budget test: EPSILON</li>
     *   <li>1 CPU and a heap of 512 MB or less: SERIAL</li>
     *   <li>a batch job: PARALLEL</li>
     *   <li>a pause budget under 10 ms with at least 4 CPUs: ZGC</li>
     *   <li>everything else: G1</li>
     * </ol>
     */
    public static Collector recommend(Workload w) {
        throw new UnsupportedOperationException("TODO: walk the decision table");
    }
}
