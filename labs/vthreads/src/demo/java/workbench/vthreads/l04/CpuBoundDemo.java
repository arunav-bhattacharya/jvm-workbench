package workbench.vthreads.l04;

import java.security.MessageDigest;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * 64 CPU-bound tasks (each hashes the same 1 MB buffer many times, a fixed amount of work)
 * on a pool sized to the cores, then with one virtual thread per task.
 *
 * <p>Args: number of tasks, hash rounds per task. Default: 64 20.
 */
public class CpuBoundDemo {
    static final byte[] DATA = new byte[1 << 20];

    public static void main(String[] args) {
        int tasks = args.length > 0 ? Integer.parseInt(args[0]) : 64;
        int rounds = args.length > 1 ? Integer.parseInt(args[1]) : 20;
        int cores = Runtime.getRuntime().availableProcessors();
        Runnable work = () -> hash(rounds);
        hash(rounds);                                    // warm up the JIT once

        time("fixed pool of " + cores + " platform threads", Executors.newFixedThreadPool(cores), tasks, work);
        time("virtual thread per task", Executors.newVirtualThreadPerTaskExecutor(), tasks, work);
    }

    static void time(String label, ExecutorService executor, int tasks, Runnable work) {
        long t0 = System.nanoTime();
        try (executor) {
            for (int i = 0; i < tasks; i++) executor.execute(work);
        }
        System.out.printf("%-34s %d tasks in %,5d ms%n", label, tasks, (System.nanoTime() - t0) / 1_000_000);
    }

    static byte[] hash(int rounds) {
        try {
            MessageDigest sha = MessageDigest.getInstance("SHA-256");
            byte[] out = null;
            for (int r = 0; r < rounds; r++) out = sha.digest(DATA);   // pure CPU, never blocks
            return out;
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }
}
