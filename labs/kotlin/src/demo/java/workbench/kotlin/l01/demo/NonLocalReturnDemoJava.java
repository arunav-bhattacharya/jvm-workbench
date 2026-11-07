package workbench.kotlin.l01.demo;

import java.util.List;

/**
 * Java twin of NonLocalReturnDemo.kt. A Java lambda is always a separate method, so `return`
 * inside it only leaves the lambda. To return from the enclosing method you need a real loop.
 */
public class NonLocalReturnDemoJava {

    static String firstDeclined(List<String> results) {
        for (String r : results) {
            if (r.startsWith("DECLINED")) return r;     // a loop, so return leaves the method
        }
        return null;
    }

    static String firstDeclinedBroken(List<String> results) {
        results.forEach(r -> {
            if (r.startsWith("DECLINED")) return;       // leaves this lambda call only
        });
        return null;                                     // always reached
    }

    static long totalUntilVoid(List<List<Long>> batches) {
        long total = 0;
        outer:
        for (List<Long> batch : batches) {
            for (long amount : batch) {
                if (amount < 0) break outer;             // Java's labeled break: Kotlin's non-local break
                total += amount;
            }
        }
        return total;
    }

    public static void main(String[] args) {
        List<String> results = List.of("APPROVED pay_1", "DECLINED pay_2 insufficient funds", "APPROVED pay_3");
        System.out.println("firstDeclined = " + firstDeclined(results));
        System.out.println("firstDeclinedBroken = " + firstDeclinedBroken(results));
        System.out.println("totalUntilVoid = " + totalUntilVoid(List.of(List.of(1_000L, 250L), List.of(400L, -1L, 900L), List.of(75L))));
    }
}
