package workbench.jmm.l02;

/** main starts a worker that adds up merchant settlements, then sleeps and reads the total. */
public class SleepIsNotJoinDemo {
    static long total;   // written by the worker, read by main

    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            long sum = 0;
            for (int merchant = 0; merchant < 20; merchant++) {
                sum += fetchSettlement(merchant);   // each call takes about 10 ms
            }
            total = sum;
        });
        worker.start();

        Thread.sleep(50);   // "plenty of time"
        System.out.printf("after sleep(50): total = %,d (expected %,d)%n", total, 20 * 100_000L);
    }

    // stands in for a call to the settlement service
    static long fetchSettlement(int merchant) {
        try {
            Thread.sleep(10);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return 100_000;
    }
}
