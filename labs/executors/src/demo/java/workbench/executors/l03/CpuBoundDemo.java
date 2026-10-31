package workbench.executors.l03;

import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/** The same CPU-bound job (32 hashing tasks) on pools of 1, 2, 4, 8 and 16 threads. */
public class CpuBoundDemo {
    // pure computation: SHA-256 over 16 MB, like signing a big settlement file. No I/O, no locks.
    static long hash(long seed) throws Exception {
        MessageDigest sha = MessageDigest.getInstance("SHA-256");
        byte[] block = new byte[16 * 1024];
        block[0] = (byte) seed;
        for (int i = 0; i < 1_000; i++) sha.update(block);
        return sha.digest()[0];
    }

    public static void main(String[] args) throws Exception {
        System.out.println("availableProcessors() = " + Runtime.getRuntime().availableProcessors());
        hash(1);                                            // warm up the JIT once
        for (int threads : new int[] {1, 2, 4, 8, 16}) {
            long t0 = System.nanoTime();
            long sum = 0;
            try (ExecutorService pool = Executors.newFixedThreadPool(threads)) {
                List<Future<Long>> parts = new ArrayList<>();
                for (int task = 0; task < 32; task++) {
                    long seed = task;
                    parts.add(pool.submit(() -> hash(seed)));
                }
                for (Future<Long> f : parts) sum += f.get();
            }
            System.out.printf("%2d threads: %,5d ms   (checksum %d)%n", threads, (System.nanoTime() - t0) / 1_000_000, sum);
        }
    }
}
