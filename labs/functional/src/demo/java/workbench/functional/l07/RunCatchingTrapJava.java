package workbench.functional.l07;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * Java equivalent of RunCatchingTrap.kt: a catch-everything block around a blocking call swallows the
 * interrupt, the thread's cancel signal, and the code after it charges the card anyway.
 */
public class RunCatchingTrapJava {
    public static void main(String[] args) throws InterruptedException {
        System.out.println("1. catch (Exception e) around sleep, interrupted after 50 ms:");
        List<String> ledger = new CopyOnWriteArrayList<>();
        Thread swallowing = new Thread(() -> {
            try {
                Thread.sleep(1_000);                                  // the issuer call
            } catch (Exception e) {
                System.out.println("  caught " + e.getClass().getSimpleName() + ", carrying on");
            }
            ledger.add("charged card");
        });
        swallowing.start();
        Thread.sleep(50);
        swallowing.interrupt();
        swallowing.join();
        System.out.println("  ledger: " + ledger);

        System.out.println("2. the same, with the interrupt restored and the work stopped:");
        List<String> ledger2 = new CopyOnWriteArrayList<>();
        Thread stopping = new Thread(() -> {
            try {
                Thread.sleep(1_000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();                   // keep the signal
                return;                                               // and stop
            }
            ledger2.add("charged card");
        });
        stopping.start();
        Thread.sleep(50);
        stopping.interrupt();
        stopping.join();
        System.out.println("  ledger: " + ledger2);
    }
}
