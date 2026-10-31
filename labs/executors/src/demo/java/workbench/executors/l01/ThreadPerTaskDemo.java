package workbench.executors.l01;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.LongAdder;

/** 5,000 tiny tasks: one new thread per task, then the same tasks on a pool of 4 threads. */
public class ThreadPerTaskDemo {
    static final LongAdder work = new LongAdder();

    static void task() {
        work.add(Long.toHexString(System.nanoTime()).length());   // a few nanoseconds of real work
    }

    public static void main(String[] args) throws Exception {
        int tasks = args.length > 0 ? Integer.parseInt(args[0]) : 5_000;
        for (int round = 1; round <= 2; round++) {
            // 1. a brand-new platform thread for every task
            long t0 = System.nanoTime();
            CountDownLatch done = new CountDownLatch(tasks);
            for (int i = 0; i < tasks; i++) {
                new Thread(() -> { task(); done.countDown(); }).start();
            }
            done.await();
            long perTask = (System.nanoTime() - t0) / 1_000_000;

            // 2. the same tasks on four threads that are created once and reused
            t0 = System.nanoTime();
            try (ExecutorService pool = Executors.newFixedThreadPool(4)) {
                for (int i = 0; i < tasks; i++) pool.execute(ThreadPerTaskDemo::task);
            }   // close() waits for all of them
            long pooled = (System.nanoTime() - t0) / 1_000_000;

            System.out.printf("round %d: %,d tasks  new thread each: %,d ms  pool of 4: %,d ms%n",
                    round, tasks, perTask, pooled);
        }
    }
}
