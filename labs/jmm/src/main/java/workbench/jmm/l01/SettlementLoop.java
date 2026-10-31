package workbench.jmm.l01;

/**
 * Runs settlement passes on its own thread until another thread calls {@link #stop()}.
 *
 * <p>The bug: once the JIT compiles {@link #run()}, the loop never sees {@code running}
 * turn false, so {@code stop()} does nothing and the thread spins forever.
 * Fix it with the smallest change that makes the write in {@code stop()} visible to the loop.
 */
public class SettlementLoop implements Runnable {
    private boolean running = true;
    private long passes;

    @Override
    public void run() {
        long n = 0;
        while (running) {   // the JIT may read this field once and keep the value in a register
            n++;            // stands in for one settlement pass
        }
        passes = n;
    }

    /** Asks the loop to finish. Called from another thread. */
    public void stop() {
        running = false;
    }

    /** How many passes ran. Only read this after joining the thread that ran {@link #run()}. */
    public long passes() {
        return passes;
    }
}
