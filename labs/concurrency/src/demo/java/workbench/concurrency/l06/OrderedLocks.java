package workbench.concurrency.l06;

/** The same opposite transfers, with every thread taking the locks in one global order. */
public class OrderedLocks {
    record Acct(int id, long[] balance) {}

    public static void main(String[] args) throws InterruptedException {
        Acct a = new Acct(1, new long[] {1_000_000});
        Acct b = new Acct(2, new long[] {1_000_000});
        Thread t1 = new Thread(() -> { for (int i = 0; i < 100_000; i++) move(a, b, 1); }, "A-to-B");
        Thread t2 = new Thread(() -> { for (int i = 0; i < 100_000; i++) move(b, a, 1); }, "B-to-A");
        long t0 = System.nanoTime();
        t1.start();
        t2.start();
        t1.join();
        t2.join();
        System.out.printf("200,000 opposite transfers in %d ms, total still %,d%n",
                (System.nanoTime() - t0) / 1_000_000, a.balance()[0] + b.balance()[0]);
    }

    static void move(Acct from, Acct to, long cents) {
        Acct first = from.id() < to.id() ? from : to;    // lower id first, whatever the direction
        Acct second = first == from ? to : from;
        synchronized (first) {
            synchronized (second) {
                from.balance()[0] -= cents;
                to.balance()[0] += cents;
            }
        }
    }
}
