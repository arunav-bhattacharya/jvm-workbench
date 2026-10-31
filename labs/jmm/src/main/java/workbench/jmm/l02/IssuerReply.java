package workbench.jmm.l02;

/**
 * Hands the card issuer's answer from the I/O thread to the request thread that is waiting for it.
 * {@link #complete} is called exactly once.
 *
 * <p>The bug: the request thread spins on a plain flag, so it may wait forever, and even when it
 * stops it has no guarantee of seeing {@code authCode}. Replace the flag with a
 * {@link java.util.concurrent.CountDownLatch}, then write a {@code // hb:} comment that names the edge.
 */
public class IssuerReply {
    private String authCode;
    private int issuerMillis;
    private boolean done;

    /** Called once, by the I/O thread, when the issuer answers. */
    public void complete(String authCode, int issuerMillis) {
        this.authCode = authCode;
        this.issuerMillis = issuerMillis;
        done = true;
    }

    /** Called by the request thread. Waits for {@link #complete}, then returns e.g. "A1B2C3 in 120 ms". */
    public String awaitReply() throws InterruptedException {
        while (!done) {
            // wait for the I/O thread
        }
        return authCode + " in " + issuerMillis + " ms";
    }
}
