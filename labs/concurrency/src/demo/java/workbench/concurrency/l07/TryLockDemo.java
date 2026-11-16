package workbench.concurrency.l07;

import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantLock;

/**
 * The end-of-day interest job holds the ledger lock for 1.5 s.
 * Three threads want in, each in a different way.
 */
public class TryLockDemo {
    static final ReentrantLock ledger = new ReentrantLock();
    static final Object monitor = new Object();          // older code still guards the ledger with this

    public static void main(String[] args) throws InterruptedException {
        Thread interest = new Thread(() -> {
            ledger.lock();
            try {
                synchronized (monitor) {                  // the job holds the lock AND the monitor
                    pause(1_500);                         // adding interest to every account
                }
            } finally {
                ledger.unlock();
            }
        }, "interest");
        interest.start();
        Thread.sleep(100);                                // let the interest job get in first

        Thread cashMachine = new Thread(() -> {
            long t0 = System.nanoTime();
            try {
                if (ledger.tryLock(200, TimeUnit.MILLISECONDS)) {      // wait at most 200 ms
                    try { System.out.println("cash-machine: got the lock"); } finally { ledger.unlock(); }
                } else {
                    System.out.printf("cash-machine: gave up after %d ms, asked the customer to try again%n",
                            (System.nanoTime() - t0) / 1_000_000);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "cash-machine");

        Thread statement = new Thread(() -> {
            try {
                ledger.lockInterruptibly();                            // an interrupt can cancel this wait
                try { System.out.println("statement: got the lock"); } finally { ledger.unlock(); }
            } catch (InterruptedException e) {
                System.out.println("statement: interrupted while waiting, gave up cleanly");
            }
        }, "statement");

        Thread teller = new Thread(() -> {
            synchronized (monitor) {                                   // no way to give up here
                System.out.println("teller: got the monitor at last, interrupted=" + Thread.currentThread().isInterrupted());
            }
        }, "teller");

        cashMachine.start();
        statement.start();
        teller.start();
        Thread.sleep(400);
        System.out.println("states: statement=" + statement.getState() + ", teller=" + teller.getState());
        statement.interrupt();                            // the program is shutting down
        teller.interrupt();
        for (Thread t : new Thread[] {cashMachine, statement, teller, interest}) t.join();
    }

    static void pause(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }
}
