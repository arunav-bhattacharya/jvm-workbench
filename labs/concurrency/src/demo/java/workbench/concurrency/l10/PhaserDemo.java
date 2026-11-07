package workbench.concurrency.l10;

import java.util.concurrent.Phaser;

/** A settlement run in three phases. One worker leaves after the first phase; the Phaser just has fewer parties. */
public class PhaserDemo {
    public static void main(String[] args) throws InterruptedException {
        String[] phases = {"fetch", "net", "post"};
        Phaser phaser = new Phaser(1) {                        // 1 party: main, until it deregisters
            @Override
            protected boolean onAdvance(int phase, int parties) {
                System.out.printf("  phase %d (%s) done, %d parties%n", phase, phases[phase], parties);
                return phase == phases.length - 1 || parties == 0;   // true ends the phaser
            }
        };
        Thread[] workers = new Thread[3];
        for (int w = 0; w < workers.length; w++) {
            int me = w;
            phaser.register();                                 // a new party joins
            workers[w] = new Thread(() -> {
                for (int p = 0; p < phases.length; p++) {
                    if (me == 2 && p == 1) {
                        phaser.arriveAndDeregister();          // worker 2 only fetches, then leaves
                        return;
                    }
                    phaser.arriveAndAwaitAdvance();            // like a barrier, for this phase
                }
            });
            workers[w].start();
        }
        phaser.arriveAndDeregister();                          // main stops taking part
        for (Thread t : workers) t.join();
        System.out.println("terminated: " + phaser.isTerminated());
    }
}
