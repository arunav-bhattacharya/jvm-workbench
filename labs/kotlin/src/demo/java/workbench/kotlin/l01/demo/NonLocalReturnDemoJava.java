package workbench.kotlin.l01.demo;

import java.util.List;

/**
 * Java twin of NonLocalReturnDemo.kt. A Java lambda is always a separate method, so `return`
 * inside it only leaves the lambda. To return from the enclosing method you need a real loop.
 */
public class NonLocalReturnDemoJava {

    static String firstJammed(List<String> log) {
        for (String line : log) {
            if (line.startsWith("JAMMED")) return line;  // a loop, so return leaves the method
        }
        return null;
    }

    static String firstJammedBroken(List<String> log) {
        log.forEach(line -> {
            if (line.startsWith("JAMMED")) return;       // leaves this lambda call only
        });
        return null;                                     // always reached
    }

    static long pagesUntilEmpty(List<List<Long>> batches) {
        long total = 0;
        outer:
        for (List<Long> batch : batches) {
            for (long pages : batch) {
                if (pages < 0) break outer;              // Java's labeled break: Kotlin's non-local break
                total += pages;
            }
        }
        return total;
    }

    public static void main(String[] args) {
        List<String> log = List.of("DONE job_1", "JAMMED job_2 in tray 2", "DONE job_3");
        System.out.println("firstJammed = " + firstJammed(log));
        System.out.println("firstJammedBroken = " + firstJammedBroken(log));
        System.out.println("pagesUntilEmpty = " + pagesUntilEmpty(List.of(List.of(1_000L, 250L), List.of(400L, -1L, 900L), List.of(75L))));
    }
}
