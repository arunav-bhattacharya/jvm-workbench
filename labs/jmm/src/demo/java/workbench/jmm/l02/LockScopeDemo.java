package workbench.jmm.l02;

/** A writer sets a balance inside a lock. A reader spins until it sees it. Which lock does the reader need? */
public class LockScopeDemo {
    static final Object LEDGER_LOCK = new Object();
    static long balance;   // meant to be guarded by LEDGER_LOCK

    public static void main(String[] args) throws InterruptedException {
        boolean shared = args.length > 0 && args[0].equals("shared");
        Thread reader = new Thread(shared ? LockScopeDemo::readWithLedgerLock : LockScopeDemo::readWithOwnLock);
        reader.setDaemon(true);   // so the JVM can exit even if the reader never stops
        reader.start();

        Thread.sleep(500);        // let the JIT compile the reader's loop
        synchronized (LEDGER_LOCK) {
            balance = 12_000;     // cents
        }
        System.out.println("writer set balance = 12000 inside synchronized (LEDGER_LOCK)");

        reader.join(3_000);
        System.out.println("reader still spinning 3 s later? " + reader.isAlive());
    }

    static void readWithOwnLock() {
        long seen;
        do {
            synchronized (new Object()) {   // a lock no other thread can ever take
                seen = balance;
            }
        } while (seen == 0);
        System.out.println("reader (own lock) saw balance = " + seen);
    }

    static void readWithLedgerLock() {
        long seen;
        do {
            synchronized (LEDGER_LOCK) {    // the same monitor the writer released
                seen = balance;
            }
        } while (seen == 0);
        System.out.println("reader (LEDGER_LOCK) saw balance = " + seen);
    }
}
