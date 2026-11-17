package workbench.functional.l06.demo;

import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** The same null handling with Optional and Objects. Note which exception each check throws. */
public class NullToolsJava {
    record Guest(String name, String favorite) {}
    record ShoppingLine(String item, Integer grams, String note) {}

    static String starterFor(Guest guest) {
        Optional<String> favorite = Optional.ofNullable(guest).map(Guest::favorite);
        if (favorite.isEmpty()) return "no favorite known: serve soup";
        return "start with " + favorite.get().toLowerCase();
    }

    public static void main(String[] args) {
        System.out.println(starterFor(new Guest("Ana", "Tomato salad")));
        System.out.println(starterFor(new Guest("Ben", null)));
        System.out.println(starterFor(null));

        // Optional.filter is the closest thing to takeIf
        int grams = 250;
        System.out.println("filter positive: " + Optional.of(grams).filter(g -> g > 0).orElse(null)
                + ", filter over 1,000: " + Optional.of(grams).filter(g -> g > 1_000).orElse(null));

        // Objects.requireNonNull throws NullPointerException; Kotlin's requireNotNull throws IllegalArgumentException
        ShoppingLine line = new ShoppingLine("flour", null, "the strong kind");
        try {
            Objects.requireNonNull(line.grams(), "shopping line " + line.item() + " has no amount");
        } catch (NullPointerException e) {
            System.out.println("requireNonNull: " + e.getClass().getSimpleName() + ": " + e.getMessage());
        }

        // mapNotNull: map, then drop the nulls
        List<ShoppingLine> lines = List.of(line, new ShoppingLine("sugar", 200, null), new ShoppingLine("eggs", null, "free range"));
        System.out.println("notes: " + lines.stream().map(ShoppingLine::note).filter(Objects::nonNull).toList());
    }
}
