package workbench.concurrency.l06;

import java.time.Duration;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;

public final class Transfers {
    private Transfers() {}

    public static void transfer(Account from, Account to, long cents) {
        // 1. one global order for every thread: lower id first, whatever the direction
        Account first = from.id() <= to.id() ? from : to;
        Account second = first == from ? to : from;
        first.lock().lock();
        try {
            second.lock().lock();           // a self-transfer takes the same lock twice: ReentrantLock allows it
            try {
                from.debit(cents);
                to.credit(cents);
            } finally {
                second.lock().unlock();
            }
        } finally {
            first.lock().unlock();
        }
    }

    public static boolean tryTransfer(Account from, Account to, long cents, Duration timeout) throws InterruptedException {
        long deadline = System.nanoTime() + timeout.toNanos();
        while (System.nanoTime() < deadline) {
            // 2. never wait long for a lock: a short tryLock breaks "no preemption"
            if (from.lock().tryLock(10, TimeUnit.MILLISECONDS)) {
                try {
                    if (to.lock().tryLock(10, TimeUnit.MILLISECONDS)) {
                        try {
                            from.debit(cents);
                            to.credit(cents);
                            return true;
                        } finally {
                            to.lock().unlock();
                        }
                    }
                } finally {
                    from.lock().unlock();   // 3. couldn't get both: let go of what we hold
                }
            }
            // 4. random back-off, so two threads don't retry in lockstep (that would be livelock)
            Thread.sleep(ThreadLocalRandom.current().nextLong(1, 10));
        }
        return false;
    }
}
