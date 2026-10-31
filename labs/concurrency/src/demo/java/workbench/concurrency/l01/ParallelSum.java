package workbench.concurrency.l01;

/** Splits a CPU-bound job over 1, 2, 4 and 8 threads and times each run. */
public class ParallelSum {
    static final int N = 400_000_000;

    public static void main(String[] args) throws InterruptedException {
        System.out.println("cores: " + Runtime.getRuntime().availableProcessors());
        for (int i = 0; i < 3; i++) timed(4);        // warm-up runs, so the JIT has compiled the loop
        for (int threads : new int[] {1, 2, 4, 8}) {
            long t0 = System.nanoTime();
            long result = timed(threads);
            System.out.printf("%d thread(s): %4d ms  (checksum %d)%n", threads, (System.nanoTime() - t0) / 1_000_000, result);
        }
    }

    static long timed(int threads) throws InterruptedException {
        long[] partial = new long[threads];
        Thread[] ts = new Thread[threads];
        int chunk = N / threads;
        for (int w = 0; w < threads; w++) {
            int slot = w, from = w * chunk, to = (w == threads - 1) ? N : from + chunk;
            ts[w] = new Thread(() -> {
                long sum = 0;
                for (int i = from; i < to; i++) sum += (i * 31L) % 7;   // pure CPU work
                partial[slot] = sum;
            });
            ts[w].start();
        }
        long total = 0;
        for (int w = 0; w < threads; w++) {
            ts[w].join();
            total += partial[w];
        }
        return total;
    }
}
