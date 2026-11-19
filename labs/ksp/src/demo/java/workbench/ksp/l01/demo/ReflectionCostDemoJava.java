package workbench.ksp.l01.demo;

import java.util.function.Supplier;
import workbench.ksp.l01.HandCardsKt;
import workbench.ksp.l01.Lamp;
import workbench.ksp.l01.ReflectionCardsKt;

// The Java twin of ReflectionCostDemo.kt: Java calling the same two Kotlin functions. HandCards.kt compiles to
// the class HandCardsKt, and the extension function Lamp.inventoryCard() becomes a static method taking the lamp.
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l01.demo.ReflectionCostDemoJava
// The timings are for teaching, from a single run: expect different numbers on your machine.
public class ReflectionCostDemoJava {

    public static void main(String[] args) {
        Lamp lamp = new Lamp("desk lamp", 1, null);
        ("warm up string building: " + lamp.getName()).length(); // so neither first call pays for it

        long start = System.nanoTime();
        String byHand = HandCardsKt.inventoryCard(lamp);
        long firstByHand = System.nanoTime() - start;
        start = System.nanoTime();
        String byReflection = ReflectionCardsKt.reflectionCard(lamp);
        long firstByReflection = System.nanoTime() - start;
        System.out.println("hand-written: " + byHand);
        System.out.println("reflection:   " + byReflection);
        System.out.println("the same card: " + byHand.equals(byReflection));

        System.out.printf("first call:     hand-written %,9d ns   reflection %,9d ns%n", firstByHand, firstByReflection);
        int calls = 2_000_000;
        for (int round = 1; round <= 3; round++) {
            double hand = timePerCall(calls, () -> HandCardsKt.inventoryCard(lamp));
            double reflection = timePerCall(calls, () -> ReflectionCardsKt.reflectionCard(lamp));
            System.out.printf("round %d per call: hand-written %,9.0f ns   reflection %,9.0f ns%n", round, hand, reflection);
        }
    }

    /** Average nanoseconds per call over {@code calls} calls (the lengths are summed so the JIT keeps the work). */
    private static double timePerCall(int calls, Supplier<String> card) {
        long sink = 0;
        long start = System.nanoTime();
        for (int i = 0; i < calls; i++) sink += card.get().length();
        long elapsed = System.nanoTime() - start;
        if (sink == 42) System.out.println("unlikely");
        return (double) elapsed / calls;
    }
}
