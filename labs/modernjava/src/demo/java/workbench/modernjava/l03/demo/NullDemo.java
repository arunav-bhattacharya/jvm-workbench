package workbench.modernjava.l03.demo;

/** What a switch does with null: at the top level, and inside a nested pattern. */
public class NullDemo {

    record Point(int x, int y) {}

    record Line(Point from, Point to) {}

    static String plain(String section) {
        return switch (section) {                  // the old rule: a null selector throws
            case "FIC" -> "fiction";
            default -> "other";
        };
    }

    static String withNull(String section) {
        return switch (section) {
            case null -> "missing";                // opt in to null
            case "FIC" -> "fiction";
            default -> "other";
        };
    }

    static String nullOrDefault(Object o) {
        return switch (o) {
            case String s -> "text " + s;
            case null, default -> "null or other"; // one arm for both
        };
    }

    static String describe(Line line) {
        return switch (line) {
            case Line(Point(var x1, var y1), Point(var x2, var y2)) when x1 == x2 -> "vertical";
            case Line(Point from, Point to) -> "other line " + from + " -> " + to;   // Point from also matches null
        };
    }

    public static void main(String[] args) {
        try {
            System.out.println(plain(null));
        } catch (NullPointerException e) {
            System.out.println("plain(null):        NullPointerException");
        }
        System.out.println("withNull(null):     " + withNull(null));
        System.out.println("nullOrDefault:      " + nullOrDefault(null) + " / " + nullOrDefault(42));
        System.out.println("line, null start:   " + describe(new Line(null, new Point(1, 1))));
    }
}
