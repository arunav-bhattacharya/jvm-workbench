package workbench.memory.l04;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/** A stand-in for a payment service under load, used by the GC demos of lessons 4 and 5. */
public final class ServiceLoad {
    static volatile Object sink;                                   // garbage goes here, so it's really allocated

    private ServiceLoad() {}

    /**
     * Runs for {@code seconds}: 5,000 short-lived request objects per round, a cache that grows to
     * {@code cacheShare} of the max heap and then sheds every other entry, and a 3 MiB buffer every 50 rounds.
     * Returns how many rounds it finished: the amount of work done.
     */
    public static int run(double seconds, double cacheShare) {
        long maxHeap = Runtime.getRuntime().maxMemory();
        List<byte[]> cache = new ArrayList<>();
        long cached = 0;
        Random random = new Random(42);
        long end = System.nanoTime() + (long) (seconds * 1e9);
        int round = 0;
        while (System.nanoTime() < end) {
            round++;
            for (int i = 0; i < 5_000; i++) sink = new byte[64 + random.nextInt(256)];     // dies young
            if (cached < maxHeap * cacheShare) {
                for (int k = 0; k < 8; k++) { cache.add(new byte[8 * 1024]); cached += 8 * 1024; }   // lives long
            } else {
                for (int i = cache.size() - 1; i >= 0; i -= 2) cached -= cache.remove(i).length;   // half-empty old regions
            }
            if (round % 50 == 0) sink = new byte[3 * 1024 * 1024];                          // a 3 MiB settlement file
        }
        return round;
    }
}
