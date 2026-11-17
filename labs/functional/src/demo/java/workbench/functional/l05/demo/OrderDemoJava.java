package workbench.functional.l05.demo;

import java.util.List;

/**
 * The same three steps in Java. Java has no eager chain, so the "List chain" collects after every step,
 * which is exactly what Kotlin's List operations do. A Stream works like a Kotlin Sequence.
 */
public class OrderDemoJava {
    enum Bake { GOLDEN, RAW, BURNT }

    record Cookie(String id, int grams, Bake bake) {}

    static final List<Cookie> TRAY = List.of(
            new Cookie("c1", 45, Bake.GOLDEN),
            new Cookie("c2", 90, Bake.RAW),
            new Cookie("c3", 50, Bake.GOLDEN),
            new Cookie("c4", 80, Bake.BURNT),
            new Cookie("c5", 30, Bake.GOLDEN));

    public static void main(String[] args) {
        System.out.println("Collect after every step:");
        List<Cookie> golden = TRAY.stream()
                .filter(c -> { System.out.println("  filter " + c.id()); return c.bake() == Bake.GOLDEN; })
                .toList();
        List<Integer> grams = golden.stream()
                .map(c -> { System.out.println("  map " + c.id()); return c.grams(); })
                .toList();
        System.out.println("  lunchbox " + grams.stream().limit(2).toList());

        System.out.println("One Stream:");
        var stream = TRAY.stream()
                .filter(c -> { System.out.println("  filter " + c.id()); return c.bake() == Bake.GOLDEN; })
                .map(c -> { System.out.println("  map " + c.id()); return c.grams(); })
                .limit(2);
        System.out.println("  built a stream, nothing has run yet");
        System.out.println("  lunchbox " + stream.toList());
    }
}
