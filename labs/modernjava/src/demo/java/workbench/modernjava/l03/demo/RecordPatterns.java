package workbench.modernjava.l03.demo;

import java.util.List;

/** Record patterns: take a record apart in the case label, nested as deep as you like. */
public class RecordPatterns {

    record Point(int x, int y) {}

    record Line(Point from, Point to) {}

    sealed interface Result<T> permits Ok, Err {}

    record Ok<T>(T value) implements Result<T> {}

    record Err<T>(String message, Throwable cause) implements Result<T> {}

    static String describe(Line line) {
        return switch (line) {
            case Line(Point(var x1, var y1), Point(int x2, int y2)) when x1 == x2 ->
                    "vertical at x=" + x1 + " len " + Math.abs(y2 - y1);
            case Line(Point(var x1, var y1), Point(var x2, var y2)) when y1 == y2 ->
                    "horizontal at y=" + y1;
            case Line(Point from, Point to) -> "diagonal " + from + "->" + to;
        };
    }

    static <T> String show(Result<T> r) {
        return switch (r) {
            case Ok<T>(var v) -> "ok " + v;                                  // T inferred for v
            case Err<T>(var msg, var cause) when cause != null ->
                    "err " + msg + " caused by " + cause.getClass().getSimpleName();
            case Err<T>(var msg, var cause) -> "err " + msg;
        };
    }

    public static void main(String[] args) {
        System.out.println(describe(new Line(new Point(1, 0), new Point(1, 5))));
        System.out.println(describe(new Line(new Point(0, 3), new Point(7, 3))));
        System.out.println(describe(new Line(new Point(0, 0), new Point(2, 2))));

        System.out.println(show(new Ok<>(List.of(1, 2))));
        System.out.println(show(new Err<>("boom", new RuntimeException())));

        Object o = new Line(new Point(0, 0), new Point(9, 9));
        if (o instanceof Line(Point(var x, var y), var to) && x == 0 && y == 0) {   // patterns in instanceof too
            System.out.println("from origin to " + to);
        }
    }
}
