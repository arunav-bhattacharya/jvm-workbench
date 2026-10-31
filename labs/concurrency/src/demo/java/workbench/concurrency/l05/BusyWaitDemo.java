package workbench.concurrency.l05;

import java.lang.management.ManagementFactory;
import java.lang.management.ThreadMXBean;

/** Two threads wait one second for the same flag. One spins, one calls wait(). Compare their CPU time. */
public class BusyWaitDemo {
    static final Object lock = new Object();
    static boolean ready;                       // guarded by lock
    static volatile boolean readyForSpinner;    // the spinner can't use the lock, so it needs volatile

    public static void main(String[] args) throws InterruptedException {
        Thread spinner = new Thread(() -> {
            while (!readyForSpinner) { }        // busy-wait: checks the flag as fast as it can
        }, "spinner");
        Thread waiter = new Thread(() -> {
            synchronized (lock) {
                while (!ready) {                // guarded block: the condition, in a loop
                    try {
                        lock.wait();            // releases lock, parks until notified
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                        return;
                    }
                }
            }
        }, "waiter");
        spinner.start();
        waiter.start();

        Thread.sleep(1_000);                    // the authorization takes a second to come back
        ThreadMXBean mx = ManagementFactory.getThreadMXBean();
        long spinCpu = mx.getThreadCpuTime(spinner.threadId()) / 1_000_000;   // measure while both still wait
        long waitCpu = mx.getThreadCpuTime(waiter.threadId()) / 1_000_000;
        readyForSpinner = true;
        synchronized (lock) {
            ready = true;
            lock.notifyAll();                   // wake the waiter; it runs once we leave this block
        }
        spinner.join();
        waiter.join();
        System.out.printf("spinner used about %d ms of CPU to wait 1 s%n", spinCpu);
        System.out.printf("waiter used about %d ms of CPU to wait 1 s%n", waitCpu);
    }
}
