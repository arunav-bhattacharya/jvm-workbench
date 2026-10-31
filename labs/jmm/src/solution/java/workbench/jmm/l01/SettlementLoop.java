package workbench.jmm.l01;

public class SettlementLoop implements Runnable {
    // volatile: every read in the loop must go to memory, and the write in stop() must reach it
    private volatile boolean running = true;
    private long passes;   // plain is fine: the reader joins the thread first (join is a happens-before edge)

    @Override
    public void run() {
        long n = 0;
        while (running) {
            n++;
        }
        passes = n;
    }

    public void stop() {
        running = false;
    }

    public long passes() {
        return passes;
    }
}
