package workbench.concurrency.l04;

public class DeclineCounter {
    // a private, final lock object: nobody else can lock it, and it never changes
    private final Object lock = new Object();
    private int declines;           // a plain int now: the lock protects it, not the other way round

    public void recordDecline() {
        synchronized (lock) {
            declines++;
        }
    }

    public int total() {
        synchronized (lock) {       // reads take the same lock, so they see the latest count
            return declines;
        }
    }
}
