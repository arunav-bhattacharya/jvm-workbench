package workbench.jmm.l03;

import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.LongAdder;

/** Four threads each add 1,000,000 to four kinds of counter. Which ones add up? */
public class VolatileCounterDemo {
    static int plain;
    static volatile int vol;
    static final AtomicInteger atomic = new AtomicInteger();
    static final LongAdder adder = new LongAdder();

    static final int THREADS = 4, PER_THREAD = 1_000_000;

    public static void main(String[] args) throws InterruptedException {
        run("plain int", () -> plain++);
        run("volatile int", () -> vol++);
        run("AtomicInteger", atomic::incrementAndGet);
        run("LongAdder", adder::increment);
        System.out.printf("expected %,d each%n", THREADS * PER_THREAD);
        System.out.printf("plain %,d   volatile %,d   atomic %,d   adder %,d%n",
                plain, vol, atomic.get(), adder.sum());
    }

    static void run(String name, Runnable increment) throws InterruptedException {
        Thread[] ts = new Thread[THREADS];
        for (int t = 0; t < THREADS; t++) {
            ts[t] = new Thread(() -> {
                for (int i = 0; i < PER_THREAD; i++) increment.run();
            }, name + "-" + t);
        }
        for (Thread t : ts) t.start();
        for (Thread t : ts) t.join();   // join: the final reads in main see every thread's writes
    }
}
