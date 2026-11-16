package workbench.concurrency.l05;

import java.lang.management.ManagementFactory;
import java.lang.management.ThreadMXBean;

/** Two cooks wait one second for the first order. One spins, one calls wait(). Compare their CPU time. */
public class BusyWaitDemo {
    static final Object lock = new Object();
    static boolean ready;                       // guarded by lock
    static volatile boolean readyForSpinner;    // the spinner can't use the lock, so it needs volatile

    public static void main(String[] args) throws InterruptedException {
        Thread spinningCook = new Thread(() -> {
            while (!readyForSpinner) { }        // busy-wait: checks the flag as fast as it can
        }, "spinning-cook");
        Thread waitingCook = new Thread(() -> {
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
        }, "waiting-cook");
        spinningCook.start();
        waitingCook.start();

        Thread.sleep(1_000);                    // the first order arrives a second later
        ThreadMXBean mx = ManagementFactory.getThreadMXBean();
        long spinCpu = mx.getThreadCpuTime(spinningCook.threadId()) / 1_000_000;   // measure while both still wait
        long waitCpu = mx.getThreadCpuTime(waitingCook.threadId()) / 1_000_000;
        readyForSpinner = true;
        synchronized (lock) {
            ready = true;
            lock.notifyAll();                   // wake the waiting cook; it runs once we leave this block
        }
        spinningCook.join();
        waitingCook.join();
        System.out.printf("the spinning cook used about %d ms of CPU to wait 1 s%n", spinCpu);
        System.out.printf("the waiting cook used about %d ms of CPU to wait 1 s%n", waitCpu);
    }
}
