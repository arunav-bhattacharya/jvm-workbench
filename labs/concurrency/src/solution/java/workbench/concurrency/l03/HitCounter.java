package workbench.concurrency.l03;

public class HitCounter {
    private int count;

    // synchronized makes read-add-write one indivisible step, and makes the new value visible
    public synchronized void hit() {
        count++;
    }

    // reads need the same lock, or a reader may see a stale value
    public synchronized int total() {
        return count;
    }
}
