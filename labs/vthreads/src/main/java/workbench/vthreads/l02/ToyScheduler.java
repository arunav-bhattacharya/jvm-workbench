package workbench.vthreads.l02;

/**
 * A one-carrier scheduler for {@link Fiber}s, with a virtual clock.
 *
 * <p>It does, in miniature, what the JDK's virtual thread scheduler does:
 * <ul>
 *   <li>a FIFO run queue of fibers that are ready;</li>
 *   <li>"mount" = take the next ready fiber and call {@code resume()} on the calling thread (the carrier);</li>
 *   <li>"unmount" = the fiber returned {@link Step.Sleep}: park it in a timer queue until {@code now + millis};</li>
 *   <li>{@link Step.Done}: drop it.</li>
 * </ul>
 * The clock is virtual. Running code takes no time. When no fiber is ready, jump the clock to the
 * earliest wake-up time and make every fiber due at that time ready, earliest first, and in the order
 * they went to sleep when the times are equal. {@code run()} returns when no fiber is ready or sleeping.
 */
public final class ToyScheduler {

    /** Adds a fiber to the back of the run queue. May be called before or during {@link #run()}. */
    public void spawn(Fiber fiber) {
        throw new UnsupportedOperationException("TODO: add the fiber to the run queue");
    }

    /** The virtual clock in milliseconds. Starts at 0. */
    public long now() {
        throw new UnsupportedOperationException("TODO: return the virtual clock");
    }

    /** Runs every fiber to completion on the calling thread. Returns how many times it called resume() (mounts). */
    public int run() {
        throw new UnsupportedOperationException("TODO: loop: mount ready fibers, park sleepers, advance the clock when nothing is ready");
    }
}
