package workbench.functional.l04.demo;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/** Java twin of ReportLoop.kt: the report as one loop, then as streams. */
public class ReportLoopJava {

    enum Status { GOLDEN, RAW, BURNT }
    record Cookie(String id, String flavor, int grams, Status status, Integer nibbledGrams) {}

    static final List<Cookie> DAY = List.of(
            new Cookie("c1", "oat", 45, Status.GOLDEN, null),
            new Cookie("c2", "chocolate", 90, Status.RAW, null),
            new Cookie("c3", "oat", 50, Status.GOLDEN, 10),
            new Cookie("c4", "ginger", 80, Status.BURNT, null),
            new Cookie("c5", "chocolate", 30, Status.GOLDEN, null));

    static int biteOf(Cookie c) { return c.nibbledGrams() == null ? 0 : c.nibbledGrams(); }

    // The loop: four results built at once, and every line changes one of them.
    static String reportLoop(List<Cookie> cookies) {
        int golden = 0;
        Map<String, Integer> net = new LinkedHashMap<>();
        List<String> burnt = new ArrayList<>();
        Cookie largest = cookies.get(0);
        for (Cookie c : cookies) {
            switch (c.status()) {
                case GOLDEN -> {
                    golden += c.grams();
                    net.merge(c.flavor(), c.grams() - biteOf(c), Integer::sum);
                    if (c.grams() > largest.grams()) largest = c;
                }
                case BURNT -> burnt.add(c.id());
                case RAW -> { }
            }
        }
        return "golden=" + golden + " net=" + net + " burnt=" + burnt + " largest=" + largest.id();
    }

    // The same report with streams. groupingBy needs LinkedHashMap::new to keep first-seen order.
    static String reportChain(List<Cookie> cookies) {
        List<Cookie> goldenCookies = cookies.stream().filter(c -> c.status() == Status.GOLDEN).toList();
        int golden = goldenCookies.stream().mapToInt(Cookie::grams).sum();
        Map<String, Integer> net = goldenCookies.stream().collect(Collectors.groupingBy(
                Cookie::flavor, LinkedHashMap::new, Collectors.summingInt(c -> c.grams() - biteOf(c))));
        List<String> burnt = cookies.stream().filter(c -> c.status() == Status.BURNT).map(Cookie::id).toList();
        String largest = goldenCookies.stream()
                .max(Comparator.comparingInt(Cookie::grams))
                .map(Cookie::id).orElse(null);
        return "golden=" + golden + " net=" + net + " burnt=" + burnt + " largest=" + largest;
    }

    public static void main(String[] args) {
        List<Cookie> cookies = args.length > 0 && args[0].equals("empty") ? List.of() : DAY;
        System.out.println("chain: " + reportChain(cookies));
        try {
            System.out.println("loop:  " + reportLoop(cookies));
        } catch (IndexOutOfBoundsException e) {
            System.out.println("loop:  threw " + e);
        }
    }
}
