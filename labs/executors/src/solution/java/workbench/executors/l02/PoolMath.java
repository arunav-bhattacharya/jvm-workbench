package workbench.executors.l02;

public final class PoolMath {
    private PoolMath() {}

    public record Outcome(int threads, int queued, int rejected) {}

    public static Outcome predict(int core, int max, int queueCapacity, int tasks) {
        int threads = 0, queued = 0, rejected = 0;
        for (int i = 0; i < tasks; i++) {
            if (threads < core) threads++;                 // 1. below core: always a new thread, even if others idle
            else if (queued < queueCapacity) queued++;     // 2. at core: queue it
            else if (threads < max) threads++;             // 3. queue full: grow toward max
            else rejected++;                               // 4. full everywhere: the RejectedExecutionHandler
        }
        return new Outcome(threads, queued, rejected);
    }
}
