package workbench.concurrency.l06;

import java.lang.management.ManagementFactory;
import java.lang.management.ThreadInfo;
import java.lang.management.ThreadMXBean;

/** Two transfers lock the same two accounts in opposite orders. Run with -Pargs=wait to keep it alive for jcmd. */
public class DeadlockDemo {
    static final Object accountA = new Object();
    static final Object accountB = new Object();

    public static void main(String[] args) throws InterruptedException {
        boolean stayAlive = args.length > 0 && args[0].equals("wait");
        Thread t1 = new Thread(() -> move(accountA, accountB), "transfer-A-to-B");
        Thread t2 = new Thread(() -> move(accountB, accountA), "transfer-B-to-A");
        t1.setDaemon(true);                  // daemon, so the JVM can still exit at the end
        t2.setDaemon(true);
        t1.start();
        t2.start();
        Thread.sleep(1_000);

        ThreadMXBean mx = ManagementFactory.getThreadMXBean();
        long[] ids = mx.findDeadlockedThreads();   // what a health check can ask the JVM
        System.out.println("deadlocked threads: " + (ids == null ? 0 : ids.length));
        if (ids != null) {
            for (ThreadInfo info : mx.getThreadInfo(ids)) {
                System.out.println("  " + info.getThreadName() + " is " + info.getThreadState()
                        + ", wants a lock held by " + info.getLockOwnerName());
            }
        }
        if (stayAlive) {
            System.out.println("pid " + ProcessHandle.current().pid() + ": run  jcmd "
                    + ProcessHandle.current().pid() + " Thread.print  in another terminal (60 s)");
            Thread.sleep(60_000);
        }
    }

    static void move(Object from, Object to) {
        synchronized (from) {
            sleep(300);                      // widen the window: the other thread takes its first lock now
            synchronized (to) {
                System.out.println(Thread.currentThread().getName() + " moved the money");
            }
        }
    }

    static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }
}
