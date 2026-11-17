package workbench.functional.l04.demo;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

/** Java twin of Operations.kt: the same operations on streams. */
public class OperationsJava {

    enum Status { GOLDEN, RAW, BURNT }
    record Cookie(String id, String flavor, int grams, Status status, Integer nibbledGrams) {}

    static final List<Cookie> DAY = List.of(
            new Cookie("c1", "oat", 45, Status.GOLDEN, null),
            new Cookie("c2", "chocolate", 90, Status.RAW, null),
            new Cookie("c3", "oat", 50, Status.GOLDEN, 10),
            new Cookie("c4", "ginger", 80, Status.BURNT, null),
            new Cookie("c5", "chocolate", 30, Status.GOLDEN, null));

    public static void main(String[] args) {
        System.out.println("map:         " + DAY.stream().map(Cookie::grams).toList());
        System.out.println("filter:      " + DAY.stream().filter(c -> c.status() == Status.GOLDEN).map(Cookie::id).toList());
        System.out.println("mapNotNull:  " + DAY.stream().map(Cookie::nibbledGrams).filter(Objects::nonNull).toList());

        List<List<Cookie>> trays = List.of(DAY.subList(0, 3), DAY.subList(3, 5));   // two trays out of the oven
        System.out.println("flatMap:     " + trays.stream().flatMap(t -> t.stream().map(Cookie::id)).toList());

        System.out.println("sumOf:       " + DAY.stream().mapToInt(Cookie::grams).sum());
        System.out.println("count:       " + DAY.stream().filter(c -> c.status() == Status.GOLDEN).count());
        System.out.println("any / all:   " + DAY.stream().anyMatch(c -> c.grams() > 75)
                + " / " + DAY.stream().allMatch(c -> c.grams() > 0));

        Map<Boolean, List<String>> split = DAY.stream().collect(Collectors.partitioningBy(
                c -> c.status() == Status.GOLDEN, Collectors.mapping(Cookie::id, Collectors.toList())));
        System.out.println("partition:   " + split.get(true) + " / " + split.get(false));

        System.out.println("toList returns: " + DAY.stream().map(Cookie::id).toList().getClass().getName());
    }
}
