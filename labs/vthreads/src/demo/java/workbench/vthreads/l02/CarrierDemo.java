package workbench.vthreads.l02;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;

/**
 * Starts some virtual threads that each print the thread they run on, sleep, and print it again.
 * A virtual thread's toString() shows its carrier after the '@'.
 *
 * <p>Args: number of virtual threads (default 8), and optionally the scheduler's parallelism.
 */
public class CarrierDemo {
    public static void main(String[] args) throws InterruptedException {
        int n = args.length > 0 ? Integer.parseInt(args[0]) : 8;
        if (args.length > 1) {
            // must be set before the first virtual thread is created
            System.setProperty("jdk.virtualThreadScheduler.parallelism", args[1]);
        }
        String[] before = new String[n];
        String[] after = new String[n];
        List<Thread> threads = new ArrayList<>();
        long t0 = System.nanoTime();
        for (int i = 0; i < n; i++) {
            int id = i;
            threads.add(Thread.ofVirtual().name("payment-" + id).start(() -> {
                before[id] = Thread.currentThread().toString();
                try {
                    Thread.sleep(50);                  // a blocking call: the thread unmounts here
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
                after[id] = Thread.currentThread().toString();
            }));
        }
        for (Thread t : threads) t.join();
        long ms = (System.nanoTime() - t0) / 1_000_000;

        Set<String> carriers = new TreeSet<>();
        int moved = 0;
        for (int i = 0; i < n; i++) {
            System.out.printf("before: %-63s after: %s%n", before[i], after[i]);
            carriers.add(carrier(before[i]));
            carriers.add(carrier(after[i]));
            if (!carrier(before[i]).equals(carrier(after[i]))) moved++;
        }
        System.out.printf("%n%d virtual threads ran on %d carrier threads %s (this machine has %d cores).%n",
                n, carriers.size(), carriers, Runtime.getRuntime().availableProcessors());
        System.out.printf("%d of them woke up on a different carrier than the one they slept on.%n", moved);
        System.out.printf("All %d finished after %d ms.%n", n, ms);
        System.out.println("Thread.currentThread().isVirtual() inside them: " + threads.get(0).isVirtual()
                + ", daemon: " + threads.get(0).isDaemon());
    }

    // "VirtualThread[#22,payment-0]/runnable@ForkJoinPool-1-worker-3" -> "ForkJoinPool-1-worker-3"
    static String carrier(String s) {
        int at = s.lastIndexOf('@');
        return at < 0 ? "(not mounted)" : s.substring(at + 1);
    }
}
