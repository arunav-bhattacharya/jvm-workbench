package workbench.performance.l01;

import java.util.ArrayList;
import java.util.List;

/**
 * Watch HotSpot compile this program. Run without arguments: it starts a second JVM with
 * -XX:+PrintCompilation and prints only the lines about this lesson's classes.
 * Pass "all" to see every line, including the JDK's own methods.
 */
public class Hot {
    interface Shape { double area(); }
    record Square(double s) implements Shape { public double area() { return s * s; } }
    record Circle(double r) implements Shape { public double area() { return Math.PI * r * r; } }
    record Tri(double b, double h) implements Shape { public double area() { return 0.5 * b * h; } }

    static double total(Shape[] shapes) {
        double sum = 0;
        for (Shape s : shapes) sum += s.area();   // one call site: first only Squares, later three types
        return sum;
    }

    static long longLoop() {                      // called once, but the loop runs 50 million times: OSR
        long acc = 0;
        for (int i = 0; i < 50_000_000; i++) acc += (i ^ (i >>> 3));
        return acc;
    }

    static void work() {
        System.out.println(longLoop());
        Shape[] squares = new Shape[1000];
        for (int i = 0; i < squares.length; i++) squares[i] = new Square(i);
        double r = 0;
        for (int i = 0; i < 20_000; i++) r += total(squares);   // only Square seen so far
        Shape[] mixed = new Shape[999];
        for (int i = 0; i < mixed.length; i++)
            mixed[i] = switch (i % 3) { case 0 -> new Square(i); case 1 -> new Circle(i); default -> new Tri(i, i); };
        for (int i = 0; i < 20_000; i++) r += total(mixed);     // two new types reach the same call site
        System.out.println(r);
    }

    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("child")) { work(); return; }
        boolean all = args.length > 0 && args[0].equals("all");
        // the same as: java -XX:+PrintCompilation -cp <classpath> workbench.performance.l01.Hot child
        String java = ProcessHandle.current().info().command().orElse("java");
        List<String> cmd = new ArrayList<>(List.of(java, "-XX:+PrintCompilation",
                "-cp", System.getProperty("java.class.path"), Hot.class.getName(), "child"));
        Process p = new ProcessBuilder(cmd).redirectErrorStream(true).start();
        try (var out = p.inputReader()) {
            out.lines()
               .filter(line -> all || line.contains("l01.Hot") || !line.contains("::"))
               .filter(line -> !line.startsWith("Picked up"))
               .forEach(System.out::println);
        }
        p.waitFor();
    }
}
