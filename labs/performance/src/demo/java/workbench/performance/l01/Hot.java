package workbench.performance.l01;

import java.util.ArrayList;
import java.util.List;

/**
 * Watch HotSpot compile this program. Run without arguments: it starts a second JVM with
 * -XX:+PrintCompilation and prints only the lines about this lesson's classes.
 * Pass "all" to see every line, including the JDK's own methods.
 */
public class Hot {
    // a document is a list of blocks, and each kind of block knows how long it takes to read
    interface Block { long millis(); }
    record Paragraph(long words) implements Block { public long millis() { return words * 250; } }        // 4 words a second
    record Heading(long words) implements Block { public long millis() { return 1_000 + words * 400; } }  // a pause, then slower
    record Quote(long words) implements Block { public long millis() { return words * 300; } }            // a little slower

    static long readingMillis(Block[] blocks) {
        long sum = 0;
        for (Block b : blocks) sum += b.millis();   // one call site: first only paragraphs, later three types
        return sum;
    }

    static long longLoop() {      // called once, but its loop runs 50 million times, like one pass over a huge book: OSR
        long acc = 0;
        for (int i = 0; i < 50_000_000; i++) acc += (i ^ (i >>> 3));
        return acc;
    }

    static void work() {
        System.out.println(longLoop());
        Block[] article = new Block[1000];
        for (int i = 0; i < article.length; i++) article[i] = new Paragraph(i);
        long r = 0;
        for (int i = 0; i < 20_000; i++) r += readingMillis(article);   // only paragraphs seen so far
        Block[] mixed = new Block[999];
        for (int i = 0; i < mixed.length; i++)
            mixed[i] = switch (i % 3) { case 0 -> new Paragraph(i); case 1 -> new Heading(i); default -> new Quote(i); };
        for (int i = 0; i < 20_000; i++) r += readingMillis(mixed);     // two new types reach the same call site
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
