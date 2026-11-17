package workbench.functional.l06.demo;

import java.util.HashSet;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import java.util.stream.Stream;

/** The same four bugs, as close as Java gets. Three of them exist in Java too; one Java's compiler prevents. */
public class ScopeBugsJava {
    enum Stage { PLANNED, COOKING }

    record Plate(String id, int servings, Stage stage) {
        Plate withStage(Stage s) { return new Plate(id, servings, s); }
    }

    static class MiniMenu {
        private final Set<String> onMenu = new HashSet<>();
        /** Returns a slot id, or null when this dish is on the menu already. */
        String add(Plate p) { return onMenu.add(p.id()) ? "slot-" + p.id() : null; }
    }

    static String planOpen(Plate open, MiniMenu menu, Supplier<Plate> suggest) {
        // Optional.map turns a null result into empty, so orElseGet runs: the same trap as ?.let ?: run
        return Optional.ofNullable(open).map(menu::add).orElseGet(() -> {
            System.out.println("    no dish open, downloading a suggestion");
            return menu.add(suggest.get());
        });
    }

    static class Timer { int minutes; }
    static class Tray { int minutes; Timer timer = new Timer(); }

    record Cake(String name, String tinId) {}
    record Tin(String name, int sizeCm) {}

    public static void main(String[] args) {
        Plate soup = new Plate("d1", 4, Stage.PLANNED);

        System.out.println("1. Optional.map(...).orElseGet(...)");
        MiniMenu menu = new MiniMenu();
        System.out.println("  first plan:  " + planOpen(soup, menu, () -> soup));
        System.out.println("  second plan: " + planOpen(soup, menu, () -> soup));

        System.out.println("2. peek drops the block's result, like also");
        Plate cooking = Stream.of(soup).peek(p -> p.withStage(Stage.COOKING)).findFirst().orElseThrow();
        System.out.println("  stage after peek { withStage }: " + cooking.stage());

        System.out.println("3. double-brace initialization, Java's nested apply");
        Tray tray = new Tray() {{ timer = new Timer() {{ minutes = 12; }}; }};
        System.out.println("  tray.minutes = " + tray.minutes + ", tray.timer.minutes = " + tray.timer.minutes);

        System.out.println("4. Java makes you name both lambda parameters, and refuses to reuse a name");
        Map<String, Cake> cakes = Map.of("k-1", new Cake("Lemon drizzle", "round-23"));
        Map<String, Tin> tins = Map.of("round-23", new Tin("springform", 23));
        String label = Optional.ofNullable(cakes.get("k-1"))
                .flatMap(cake -> Optional.ofNullable(tins.get(cake.tinId()))
                        .map(tin -> cake.name() + ": " + tin.sizeCm() + " cm tin"))
                .orElse(null);
        System.out.println("  label: " + label);
    }
}
