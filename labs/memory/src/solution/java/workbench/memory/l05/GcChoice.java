package workbench.memory.l05;

import java.util.ArrayList;
import java.util.List;

public final class GcChoice {
    private GcChoice() {}

    private static final String UNLOCK = "-XX:+UnlockExperimentalVMOptions";

    public static Collector defaultCollector(int jdk, int cpus, long memoryMb) {
        if (jdk >= 27) return Collector.G1;                           // JDK 27: G1 in all environments
        boolean serverClass = cpus >= 2 && memoryMb >= 2048 - 256;    // os::is_server_class_machine()
        return serverClass ? Collector.G1 : Collector.SERIAL;         // small containers silently get Serial
    }

    public static List<String> flagsFor(Collector collector, int jdk) {
        List<String> flags = new ArrayList<>();
        switch (collector) {
            case SERIAL -> flags.add("-XX:+UseSerialGC");
            case PARALLEL -> flags.add("-XX:+UseParallelGC");
            case G1 -> flags.add("-XX:+UseG1GC");
            case ZGC -> {
                flags.add("-XX:+UseZGC");
                if (jdk < 23) flags.add("-XX:+ZGenerational");        // generational is the default from 23, the only mode from 24
            }
            case SHENANDOAH -> flags.add("-XX:+UseShenandoahGC");
            case SHENANDOAH_GENERATIONAL -> {
                if (jdk < 24) throw new IllegalArgumentException("generational Shenandoah needs JDK 24 or later");
                if (jdk == 24) flags.add(UNLOCK);                     // experimental in 24, product in 25
                flags.add("-XX:+UseShenandoahGC");
                flags.add("-XX:ShenandoahGCMode=generational");
            }
            case EPSILON -> {
                flags.add(UNLOCK);                                    // must come before the experimental flag
                flags.add("-XX:+UseEpsilonGC");
            }
        }
        return List.copyOf(flags);
    }

    public static Collector recommend(Workload w) {
        if (w.kind() == Workload.Kind.ALLOCATION_TEST) return Collector.EPSILON;
        if (w.cpus() <= 1 && w.heapMb() <= 512) return Collector.SERIAL;   // no spare core for concurrent GC threads
        if (w.kind() == Workload.Kind.BATCH) return Collector.PARALLEL;    // throughput over pause length
        if (w.pauseBudgetMs() < 10 && w.cpus() >= 4) return Collector.ZGC; // sub-millisecond pauses, paid in CPU
        return Collector.G1;
    }
}
