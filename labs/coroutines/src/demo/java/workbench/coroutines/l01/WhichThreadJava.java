// Java equivalent of WhichThread.kt: virtual threads also move between carrier threads.
// A plain method runs on its caller's thread; a virtual thread that sleeps may wake up on another carrier.
package workbench.coroutines.l01;

import java.util.ArrayList;
import java.util.List;

public class WhichThreadJava {
    static int scaleRecipe(List<Integer> gramsForFour, int guests) {   // the same code as the Kotlin suspend fun: it never pauses
        int total = 0;
        for (int g : gramsForFour) total += g * guests / 4;
        return total;
    }

    // a virtual thread prints as VirtualThread[#29]/runnable@ForkJoinPool-1-worker-3; keep the carrier part
    static String carrier() {
        String s = Thread.currentThread().toString();
        int at = s.indexOf('@');
        return at < 0 ? Thread.currentThread().getName() : s.substring(at + 1).replace("ForkJoinPool-1-", "");
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("main runs on " + Thread.currentThread().getName());
        System.out.println("scaleRecipe says " + scaleRecipe(List.of(400, 250, 120, 30), 10) + " g, computed on "
            + Thread.currentThread().getName());

        List<Thread> dishes = new ArrayList<>();
        for (int id = 0; id < 4; id++) {
            int dish = id;
            dishes.add(Thread.ofVirtual().start(() -> {
                List<String> seen = new ArrayList<>();
                for (int step = 0; step < 4; step++) {
                    seen.add(carrier());
                    try { Thread.sleep(20); } catch (InterruptedException e) { return; } // unmounts; any carrier may resume it
                }
                System.out.println("dish " + dish + " ran on " + String.join(" -> ", seen));
            }));
        }
        for (Thread t : dishes) t.join();
    }
}
