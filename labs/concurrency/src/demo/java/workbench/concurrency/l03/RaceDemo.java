package workbench.concurrency.l03;

/** Two threads each add 1,000,000 to a shared counter. Watch what comes out. */
public class RaceDemo {
    // volatile only stops the JIT from keeping count in a register, which would hide the race.
    // It does NOT make count++ safe. The memory model track explains why.
    static volatile int count = 0;

    public static void main(String[] args) throws InterruptedException {
        int perThread = args.length > 0 ? Integer.parseInt(args[0]) : 1_000_000;
        for (int run = 1; run <= 5; run++) {
            count = 0;
            Runnable work = () -> {
                for (int i = 0; i < perThread; i++) count++;
            };
            Thread a = new Thread(work), b = new Thread(work);
            a.start(); b.start();
            a.join(); b.join();
            System.out.printf("run %d: expected %,d, got %,d (lost %,d)%n", run, 2 * perThread, count, 2 * perThread - count);
        }
    }
}
