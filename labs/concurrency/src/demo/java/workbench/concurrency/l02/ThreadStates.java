package workbench.concurrency.l02;

/** Puts threads into each of the six states and prints what getState() reports. */
public class ThreadStates {
    static final Object monitor = new Object();
    static volatile boolean spin = true;

    public static void main(String[] args) throws Exception {
        Thread sleeper = new Thread(() -> pause(2_000), "sleeper");
        System.out.printf("%-24s%s%n", "before start():", sleeper.getState());
        sleeper.start();
        show(sleeper, Thread.State.TIMED_WAITING, "inside sleep(2000):");

        Thread busy = new Thread(() -> { while (spin) Thread.onSpinWait(); }, "busy");
        busy.start();
        show(busy, Thread.State.RUNNABLE, "in a busy loop:");

        Thread waiter = new Thread(() -> {
            synchronized (monitor) {
                try {
                    monitor.wait();                      // no timeout
                } catch (InterruptedException e) {
                    System.out.println("waiter interrupted, flag now " + Thread.currentThread().isInterrupted());
                }
            }
        }, "waiter");
        waiter.start();
        show(waiter, Thread.State.WAITING, "inside wait():");

        Thread blocked = new Thread(() -> { synchronized (monitor) { } }, "blocked");
        synchronized (monitor) {                         // main holds the monitor...
            blocked.start();                             // ...so this thread cannot enter
            show(blocked, Thread.State.BLOCKED, "entering a held lock:");
        }

        spin = false;
        waiter.interrupt();
        for (Thread t : new Thread[] {sleeper, busy, waiter, blocked}) t.interrupt();
        for (Thread t : new Thread[] {sleeper, busy, waiter, blocked}) t.join();
        System.out.printf("%-24s%s%n", "after join():", sleeper.getState());
    }

    // getState() is a snapshot, so poll until the thread gets where we sent it
    static void show(Thread t, Thread.State expected, String label) throws InterruptedException {
        for (int i = 0; i < 200 && t.getState() != expected; i++) Thread.sleep(10);
        System.out.printf("%-24s%s%n", label, t.getState());
    }

    static void pause(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }
}
