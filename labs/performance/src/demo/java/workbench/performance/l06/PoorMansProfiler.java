package workbench.performance.l06;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * A sampling profiler in 40 lines: every 10 ms, take the stack of each worker thread with
 * Thread.getStackTrace() and count it. Writes the samples as collapsed stacks, the text format
 * flame graph tools read, to build/poor-man.collapsed.
 */
public class PoorMansProfiler {
    public static void main(String[] args) throws Exception {
        long until = System.nanoTime() + 4_000_000_000L;
        Thread work = new Thread(() -> {
            try { SlowFees.hammer(2, until); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        work.start();

        Map<String, Long> stacks = new HashMap<>();                 // "frame;frame;frame" -> samples
        while (work.isAlive()) {
            Thread.sleep(10);
            for (Thread t : Thread.getAllStackTraces().keySet()) {
                if (!t.getName().startsWith("fees-")) continue;
                StackTraceElement[] st = t.getStackTrace();         // the JVM must pause t to walk its stack
                if (st.length == 0) continue;
                List<String> frames = new ArrayList<>();
                for (int i = st.length - 1; i >= 0; i--)           // root first, as flame graphs want
                    frames.add(st[i].getClassName() + "." + st[i].getMethodName());
                stacks.merge(String.join(";", frames), 1L, Long::sum);
            }
        }
        write(stacks, Path.of("build", "poor-man.collapsed"));

        Map<String, Long> self = new HashMap<>();                   // top frame = where the thread was
        stacks.forEach((k, v) -> self.merge(k.substring(k.lastIndexOf(';') + 1), v, Long::sum));
        long total = self.values().stream().mapToLong(Long::longValue).sum();
        System.out.println(total + " samples; top frames:");
        self.entrySet().stream().sorted(Map.Entry.<String, Long>comparingByValue().reversed()).limit(6)
            .forEach(e -> System.out.printf("  %5.1f%%  %s%n", 100.0 * e.getValue() / total, e.getKey()));
    }

    static void write(Map<String, Long> stacks, Path file) throws IOException {
        Files.createDirectories(file.getParent());
        List<String> lines = new ArrayList<>();
        stacks.forEach((k, v) -> lines.add(k + " " + v));
        Files.write(file, lines);
        System.out.println("collapsed stacks written to " + file.toAbsolutePath());
    }
}
