package workbench.concurrency.l04;

/** A transfer thread moves money under a lock. An auditor adds up the two balances, with or without it. */
public class AuditDemo {
    static final Object lock = new Object();
    // volatile only so the JIT re-reads the fields on every pass; it does not make the pair consistent
    static volatile long a = 1_000, b = 1_000;

    public static void main(String[] args) throws InterruptedException {
        boolean auditorLocks = args.length > 0 && args[0].equals("locked");
        Thread transfers = new Thread(() -> {
            for (int i = 0; i < 200_000; i++) {
                synchronized (lock) {        // debit and credit as one step
                    a -= 50;
                    b += 50;
                }
                synchronized (lock) {        // and move it back
                    a += 50;
                    b -= 50;
                }
            }
        });
        Thread auditor = new Thread(() -> {
            long audits = 0, wrong = 0;
            while (transfers.isAlive()) {
                long total;
                if (auditorLocks) {
                    synchronized (lock) { total = a + b; }
                } else {
                    total = a + b;           // reads a, then b, while transfers may run in between
                }
                audits++;
                if (total != 2_000) wrong++;
            }
            System.out.printf("auditor %s the lock: %,d audits, %,d saw a total other than 2,000%n",
                    auditorLocks ? "took" : "skipped", audits, wrong);
        });
        transfers.start();
        auditor.start();
        transfers.join();
        auditor.join();
    }
}
