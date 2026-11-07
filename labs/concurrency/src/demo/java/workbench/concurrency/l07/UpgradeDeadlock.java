package workbench.concurrency.l07;

import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantReadWriteLock;

/**
 * One thread, one ReentrantReadWriteLock. Upgrading (read, then write) never succeeds.
 * Downgrading (write, then read, then release the write) is allowed.
 * Run with -Pargs=hang to use lock() instead of tryLock() and see the thread wait forever.
 */
public class UpgradeDeadlock {
    public static void main(String[] args) throws InterruptedException {
        ReentrantReadWriteLock rw = new ReentrantReadWriteLock();
        boolean hang = args.length > 0 && args[0].equals("hang");

        // 1. the "upgrade": ask for the write lock while still holding the read lock
        rw.readLock().lock();
        try {
            System.out.println("holding the read lock, read holds = " + rw.getReadHoldCount());
            if (hang) {
                System.out.println("calling writeLock().lock() ... (pid " + ProcessHandle.current().pid() + ", Ctrl+C to stop)");
                rw.writeLock().lock();                                  // waits for every reader to leave, us included
            }
            boolean got = rw.writeLock().tryLock(1, TimeUnit.SECONDS);  // the same wait, with a time limit
            System.out.println("write lock while holding a read lock, after 1 s: " + got);
        } finally {
            rw.readLock().unlock();
        }

        // 2. the downgrade: write lock, then read lock, then let go of the write lock
        rw.writeLock().lock();
        try {
            rw.readLock().lock();                                       // allowed: we are the only writer
        } finally {
            rw.writeLock().unlock();
        }
        try {
            System.out.println("downgraded: write locked = " + rw.isWriteLocked() + ", read holds = " + rw.getReadHoldCount());
        } finally {
            rw.readLock().unlock();
        }
    }
}
