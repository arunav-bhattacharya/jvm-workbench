package workbench.concurrency.l06;

/** Two polite diners share one spoon. Each hands it over while the other is hungry. Try -Pargs=fixed. */
public class LivelockDemo {
    static volatile int spoonOwner = 0;                 // diner 0 or diner 1
    static final boolean[] hungry = {true, true};       // written by its owner only, read by the other
    static volatile boolean stop;
    static final long[] handovers = new long[2];

    public static void main(String[] args) throws InterruptedException {
        boolean fixed = args.length > 0 && args[0].equals("fixed");
        Thread d0 = new Thread(() -> dine(0, fixed), "diner-0");
        Thread d1 = new Thread(() -> dine(1, fixed), "diner-1");
        d0.start();
        d1.start();
        d0.join(1_000);
        d1.join(1_000);
        stop = true;
        d0.join();
        d1.join();
        System.out.printf("spoon handed over %,d times; meals eaten: %d%n",
                handovers[0] + handovers[1], (hungry[0] ? 0 : 1) + (hungry[1] ? 0 : 1));
    }

    static void dine(int me, boolean fixed) {
        int other = 1 - me;
        int politeTurns = 0;
        while (!stop) {
            if (spoonOwner != me) {                     // not my spoon: wait for it
                Thread.onSpinWait();
                continue;
            }
            boolean otherHungry;
            synchronized (hungry) { otherHungry = hungry[other]; }
            if (otherHungry && (!fixed || politeTurns < 3)) {
                politeTurns++;
                handovers[me]++;
                spoonOwner = other;                     // "you first": both keep saying it
                continue;
            }
            synchronized (hungry) { hungry[me] = false; } // eat
            spoonOwner = other;                         // then pass the spoon on
            return;
        }
    }
}
