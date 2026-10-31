package workbench.concurrency.l01;

/** Creates, starts and joins thousands of threads that do nothing, and reports the average cost. */
public class ThreadCost {
    public static void main(String[] args) throws InterruptedException {
        int n = args.length > 0 ? Integer.parseInt(args[0]) : 10_000;
        for (int round = 1; round <= 3; round++) {
            long t0 = System.nanoTime();
            for (int i = 0; i < n; i++) {
                Thread t = new Thread(() -> { });
                t.start();
                t.join();
            }
            long micros = (System.nanoTime() - t0) / 1_000;
            System.out.printf("round %d: %,d threads in %,d ms, about %d microseconds each%n",
                    round, n, micros / 1_000, micros / n);
        }
    }
}
