package workbench.bytecode.l01;

import java.lang.management.ManagementFactory;
import java.util.List;

/** Two static initializers that need each other, started from two threads. */
public class InitDeadlockDemo {
    static class FxRates {
        static final long EUR_USD;
        static { pause(); EUR_USD = Fees.CARD_BPS + 108_000; }   // needs Fees
    }

    static class Fees {
        static final long CARD_BPS;
        static { pause(); CARD_BPS = FxRates.EUR_USD / 1_000; }  // needs FxRates
    }

    static void pause() {
        try { Thread.sleep(200); } catch (InterruptedException e) { throw new RuntimeException(e); }
    }

    public static void main(String[] args) throws Exception {
        Thread a = new Thread(() -> System.out.println(FxRates.EUR_USD), "rates");
        Thread b = new Thread(() -> System.out.println(Fees.CARD_BPS), "fees");
        a.setDaemon(true);   // daemon, so the JVM can still exit at the end
        b.setDaemon(true);
        a.start();
        b.start();
        Thread.sleep(1_000);

        for (Thread t : List.of(a, b)) {
            System.out.printf("%-5s state=%s at %s%n", t.getName(), t.getState(), t.getStackTrace()[0]);
        }
        long[] stuck = ManagementFactory.getThreadMXBean().findDeadlockedThreads();
        System.out.println("deadlock detector: " + (stuck == null ? "found nothing" : stuck.length + " threads"));

        if (args.length > 0) {   // -Pargs=wait gives you 30 s to run jstack
            System.out.println("jstack " + ProcessHandle.current().pid() + "   (search for 'Class initialization monitor')");
            Thread.sleep(30_000);
        }
    }
}
