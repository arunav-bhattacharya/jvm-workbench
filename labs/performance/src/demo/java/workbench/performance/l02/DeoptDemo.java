package workbench.performance.l02;

import java.util.ArrayList;
import java.util.List;

/**
 * Adds up the reading time of a document in three phases: paragraphs only, then a folded block
 * appears, then headings and quotes appear. Run it: a second JVM starts with -XX:+PrintCompilation
 * and -Xlog:deoptimization=debug, and the demo prints what happened to readingMillis().
 */
public class DeoptDemo {
    interface Block { long millis(); }   // how long one block of a document takes to read
    record Paragraph(long words) implements Block { public long millis() { return words * 250; } }
    record Heading(long words) implements Block { public long millis() { return 1_000 + words * 400; } }
    record Quote(long words) implements Block { public long millis() { return words * 300; } }

    static final long GLANCE_MILLIS = 200;   // a folded block, such as a hidden spoiler, costs only a glance

    static long readingMillis(Block[] blocks, boolean[] folded) {
        long total = 0;
        for (int i = 0; i < blocks.length; i++) {
            long ms = blocks[i].millis();         // call site: which types has it seen?
            if (folded[i]) total += GLANCE_MILLIS; // branch: has it ever been taken?
            else total += ms;
        }
        return total;
    }

    static void work() {
        int n = 1_000;
        Block[] blocks = new Block[n];
        boolean[] folded = new boolean[n];
        for (int i = 0; i < n; i++) blocks[i] = new Paragraph(20 + i % 80);
        long total = 0;

        System.out.println("phase 1: paragraphs only");
        for (int r = 0; r < 3_000; r++) total += readingMillis(blocks, folded);

        System.out.println("phase 2: one folded block per document");
        folded[500] = true;
        for (int r = 0; r < 3_000; r++) total += readingMillis(blocks, folded);

        System.out.println("phase 3: headings and quotes arrive");
        for (int i = 0; i < n; i += 3) blocks[i] = new Heading(6);
        for (int i = 1; i < n; i += 3) blocks[i] = new Quote(40);
        for (int r = 0; r < 3_000; r++) total += readingMillis(blocks, folded);
        System.out.println("done, checksum " + total);
    }

    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("child")) { work(); return; }
        String java = ProcessHandle.current().info().command().orElse("java");
        List<String> cmd = new ArrayList<>(List.of(java, "-XX:+PrintCompilation", "-Xlog:deoptimization=debug",
                "-cp", System.getProperty("java.class.path"), DeoptDemo.class.getName(), "child"));
        Process p = new ProcessBuilder(cmd).redirectErrorStream(true).start();
        try (var out = p.inputReader()) {
            out.lines()
               .filter(l -> l.contains("DeoptDemo::readingMillis") || l.contains("DeoptDemo.readingMillis") || l.startsWith("phase") || l.startsWith("done"))
               .map(l -> l.replaceAll(" pc=.*", ""))            // drop machine addresses
               .forEach(System.out::println);
        }
        p.waitFor();
    }
}
