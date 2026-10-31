package workbench.jmm.l01;

/** A worker spins until main sets a plain boolean. Does it ever notice? */
public class StopFlagDemo {
    static boolean stop;   // plain field: no volatile, no lock

    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            long spins = 0;
            while (!stop) {
                spins++;
            }
            System.out.printf("worker saw stop after %,d spins%n", spins);
        });
        worker.setDaemon(true);   // so the JVM can exit even if the worker never stops
        worker.start();

        Thread.sleep(1_000);      // give the JIT time to compile the loop
        stop = true;
        System.out.println("main set stop = true");

        worker.join(3_000);
        System.out.println("worker still running 3 s later? " + worker.isAlive());
    }
}
