package workbench.memory.l05;

/**
 * What a JVM has to run.
 *
 * @param kind            an online service, a batch job, or a test that checks an allocation budget
 * @param cpus            CPUs the container gives the JVM
 * @param heapMb          the heap you plan to give it
 * @param pauseBudgetMs   the longest GC pause the service can take without breaking its latency target
 */
public record Workload(Kind kind, int cpus, long heapMb, int pauseBudgetMs) {
    public enum Kind { SERVICE, BATCH, ALLOCATION_TEST }
}
