package workbench.performance.l04;

/**
 * Two threads, each incrementing its OWN volatile counter 25 million times.
 * Run 1: the two counters sit next to each other. Run 2: they are padded apart.
 * Whether you see a difference depends on your CPU and where the OS puts the threads.
 */
public class FalseSharingDemo {
    // the two counters in one 32-byte object: almost certainly on the same 64-byte cache line
    static final class Adjacent {
        volatile long card;
        volatile long sepa;
    }

    // superclass fields come first, so the padding class sits between card and sepa
    static class CardField { volatile long card; }
    static class Pad1 extends CardField { long p1, p2, p3, p4, p5, p6, p7, p8; }
    static class SepaField extends Pad1 { volatile long sepa; }
    static final class Padded extends SepaField { long q1, q2, q3, q4, q5, q6, q7, q8; }

    static final int N = 25_000_000;

    static long run(Runnable a, Runnable b) throws InterruptedException {
        Thread t1 = new Thread(a), t2 = new Thread(b);
        long t0 = System.nanoTime();
        t1.start(); t2.start();
        t1.join(); t2.join();
        return (System.nanoTime() - t0) / 1_000_000;
    }

    public static void main(String[] args) throws InterruptedException {
        for (int round = 1; round <= 3; round++) {
            Adjacent adj = new Adjacent();
            long msAdjacent = run(() -> { for (int i = 0; i < N; i++) adj.card++; },
                                  () -> { for (int i = 0; i < N; i++) adj.sepa++; });
            Padded pad = new Padded();
            long msPadded = run(() -> { for (int i = 0; i < N; i++) pad.card++; },
                                () -> { for (int i = 0; i < N; i++) pad.sepa++; });
            System.out.printf("round %d: adjacent %,5d ms   padded %,5d ms   (counts %d/%d, %d/%d)%n",
                    round, msAdjacent, msPadded, adj.card, adj.sepa, pad.card, pad.sepa);
        }
    }
}
