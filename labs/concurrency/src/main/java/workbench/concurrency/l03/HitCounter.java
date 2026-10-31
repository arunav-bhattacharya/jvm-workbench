package workbench.concurrency.l03;

/**
 * Counts page hits. Many request threads call {@link #hit()} at once.
 *
 * <p>This version loses updates under load. Make {@code hit()} and {@code total()}
 * safe to call from many threads.
 */
public class HitCounter {
    private int count;

    public void hit() {
        count++;                 // read, add one, write: three steps
    }

    public int total() {
        return count;
    }
}
