package workbench.jmm.l02;

import java.util.concurrent.CountDownLatch;

public class IssuerReply {
    private String authCode;      // plain fields are fine: the latch orders them
    private int issuerMillis;
    private final CountDownLatch done = new CountDownLatch(1);

    public void complete(String authCode, int issuerMillis) {
        this.authCode = authCode;          // 1. write the data
        this.issuerMillis = issuerMillis;
        done.countDown();                  // 2. release: everything above travels with it
    }

    // hb: actions before countDown() happen-before actions after a successful await() on the same latch
    public String awaitReply() throws InterruptedException {
        done.await();                      // 3. acquire: blocks (no spinning) until countDown()
        return authCode + " in " + issuerMillis + " ms";
    }
}
