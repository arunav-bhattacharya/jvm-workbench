package workbench.concurrency.l04;

/**
 * Counts card declines across all request threads.
 *
 * <p>Every method is "synchronized", yet the count comes up short under load, and javac prints a
 * {@code [synchronization]} warning when it compiles this file. Find out why, and fix the class
 * so that {@link #recordDecline()} and {@link #total()} are safe from many threads.
 * Keep using {@code synchronized}; just lock on the right thing.
 */
public class DeclineCounter {
    private Integer declines = 0;

    public void recordDecline() {
        synchronized (declines) {   // locks whatever Integer object the field points to right now
            declines++;             // ...and this line makes the field point to a different one
        }
    }

    public int total() {
        synchronized (declines) {
            return declines;
        }
    }
}
