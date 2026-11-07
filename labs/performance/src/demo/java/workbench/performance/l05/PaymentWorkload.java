package workbench.performance.l05;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

/** Four threads authorizing payments for a few seconds: CPU work, allocation, a slow issuer and a shared lock. */
public final class PaymentWorkload {
    private static final Object LEDGER = new Object();

    private PaymentWorkload() { }

    static long fee(String amount) {                       // allocates: BigDecimal parsing and arithmetic
        return new BigDecimal(amount).multiply(new BigDecimal("0.029"))
                .setScale(2, RoundingMode.HALF_EVEN).unscaledValue().longValue();
    }

    static boolean callIssuer(String merchant, long cents) throws InterruptedException {
        IssuerCallEvent event = new IssuerCallEvent();
        event.begin();
        Thread.sleep(ThreadLocalRandom.current().nextInt(2, merchant.equals("m_7") ? 40 : 12));   // m_7's issuer is slow
        boolean approved = cents < 400_000;
        event.end();
        if (event.shouldCommit()) {                         // skip the field work when no recording wants it
            event.merchant = merchant;
            event.amountCents = cents;
            event.approved = approved;
            event.commit();
        }
        return approved;
    }

    static void authorizeLoop(int worker, long untilNanos) {
        long sink = 0;
        int i = 0;
        try {
            while (System.nanoTime() < untilNanos) {
                for (int k = 0; k < 2_000; k++) sink += fee((100 + (k + i) % 9_000) + ".25");
                String merchant = "m_" + (i % 10);
                long cents = 1_000 + (i * 7_919L) % 500_000;
                callIssuer(merchant, cents);
                if (i % 25 == worker) {
                    synchronized (LEDGER) { Thread.sleep(15); }   // a ledger write that holds a shared lock
                }
                i++;
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        if (sink == 42) System.out.println();
    }

    static void run(int seconds) throws InterruptedException {
        long until = System.nanoTime() + seconds * 1_000_000_000L;
        List<Thread> threads = new ArrayList<>();
        for (int w = 0; w < 4; w++) {
            int worker = w;
            Thread t = new Thread(() -> authorizeLoop(worker, until), "auth-" + w);
            t.start();
            threads.add(t);
        }
        for (Thread t : threads) t.join();
    }
}
