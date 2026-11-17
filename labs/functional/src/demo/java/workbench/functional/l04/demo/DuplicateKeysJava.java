package workbench.functional.l04.demo;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/** Java twin of DuplicateKeys.kt. Same data, different defaults: no key order, and toMap throws. */
public class DuplicateKeysJava {

    enum Status { GOLDEN, RAW, BURNT }
    record Cookie(String id, String flavor, int grams, Status status, Integer nibbledGrams) {}

    static final List<Cookie> DAY = List.of(
            new Cookie("c1", "oat", 45, Status.GOLDEN, null),
            new Cookie("c2", "chocolate", 90, Status.RAW, null),
            new Cookie("c3", "oat", 50, Status.GOLDEN, 10),
            new Cookie("c4", "ginger", 80, Status.BURNT, null),
            new Cookie("c5", "chocolate", 30, Status.GOLDEN, null));

    public static void main(String[] args) {
        Map<String, List<String>> byFlavor = DAY.stream().collect(
                Collectors.groupingBy(Cookie::flavor, Collectors.mapping(Cookie::id, Collectors.toList())));
        System.out.println("groupingBy:   " + byFlavor);
        System.out.println("map class:    " + byFlavor.getClass().getName());

        // One value per key. oat and chocolate each have two cookies.
        try {
            System.out.println("toMap:        " + DAY.stream().collect(Collectors.toMap(Cookie::flavor, Cookie::id)));
        } catch (IllegalStateException e) {
            System.out.println("toMap:        threw " + e);
        }

        // Counting per key.
        System.out.println("counting:     " + DAY.stream().collect(
                Collectors.groupingBy(Cookie::flavor, Collectors.counting())));
    }
}
