package workbench.performance.l02;

import java.util.ArrayList;
import java.util.List;

/**
 * Two versions of the same word-count check. One builds its error message inline, the other moves
 * the cold path into a helper. Run it: a second JVM starts with -XX:+PrintInlining and the demo
 * prints what C1 and C2 decided at the two call sites in summarize().
 */
public class InliningDemo {
    static final long MAX_WORDS = 10_000_000L;

    // the error message is built right here, so its bytecode counts against the inlining budget
    static long requireWordCountInline(long words) {
        if (words <= 0 || words > MAX_WORDS) {
            throw new IllegalArgumentException(
                    String.format("word count must be between 1 and %d, got %d", MAX_WORDS, words));
        }
        return words;
    }

    // same check, but the cold path lives in its own method
    static long requireWordCountSplit(long words) {
        if (words <= 0 || words > MAX_WORDS) throw badWordCount(words);
        return words;
    }

    static IllegalArgumentException badWordCount(long words) {
        return new IllegalArgumentException(
                String.format("word count must be between 1 and %d, got %d", MAX_WORDS, words));
    }

    // a summary is about a tenth of the text; each check runs on 1 call in 8, so neither call site is hot for C2
    static long summarize(long words, int i) {
        long r = words / 10;
        if ((i & 7) == 0) r += requireWordCountInline(words);
        if ((i & 7) == 1) r += requireWordCountSplit(words);
        return r;
    }

    static void work() {
        long s = 0;
        for (int i = 0; i < 2_000_000; i++) s += summarize(1_000 + (i & 1023), i);
        System.out.println("checksum " + s);
    }

    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("child")) { work(); return; }
        String java = ProcessHandle.current().info().command().orElse("java");
        List<String> cmd = new ArrayList<>(List.of(java,
                "-XX:+UnlockDiagnosticVMOptions", "-XX:+PrintInlining", "-XX:+PrintCompilation",
                "-cp", System.getProperty("java.class.path"), InliningDemo.class.getName(), "child"));
        Process p = new ProcessBuilder(cmd).redirectErrorStream(true).start();
        try (var out = p.inputReader()) {
            // keep the compile lines for summarize() and the decisions about the two checks
            out.lines()
               .filter(l -> l.contains("InliningDemo::summarize (") || l.contains("requireWordCount") || l.startsWith("checksum"))
               .forEach(System.out::println);
        }
        p.waitFor();
    }
}
