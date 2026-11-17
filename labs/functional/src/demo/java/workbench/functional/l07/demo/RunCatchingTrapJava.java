package workbench.functional.l07.demo;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * Java equivalent of RunCatchingTrap.kt: a catch-everything block around a blocking call swallows the
 * interrupt, the thread's stop signal, and the code after it places the order anyway.
 */
public class RunCatchingTrapJava {
    public static void main(String[] args) throws InterruptedException {
        System.out.println("1. catch (Exception e) around sleep, interrupted after 50 ms:");
        List<String> placed = new CopyOnWriteArrayList<>();
        Thread swallowing = new Thread(() -> {
            try {
                Thread.sleep(1_000);                                  // waiting for the shop
            } catch (Exception e) {
                System.out.println("  caught " + e.getClass().getSimpleName() + ", carrying on");
            }
            placed.add("placed the order");
        });
        swallowing.start();
        Thread.sleep(50);
        swallowing.interrupt();
        swallowing.join();
        System.out.println("  orders: " + placed);

        System.out.println("2. the same, with the interrupt restored and the work stopped:");
        List<String> placed2 = new CopyOnWriteArrayList<>();
        Thread stopping = new Thread(() -> {
            try {
                Thread.sleep(1_000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();                   // keep the signal
                return;                                               // and stop
            }
            placed2.add("placed the order");
        });
        stopping.start();
        Thread.sleep(50);
        stopping.interrupt();
        stopping.join();
        System.out.println("  orders: " + placed2);
    }
}
