package workbench.concurrency.l09;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/** Memoized Fibonacci where the mapping function calls back into the same map. The Javadoc forbids it. */
public class RecursiveUpdate {
    static Map<Integer, Long> memo;

    static long fib(int n) {
        if (n < 2) return n;
        return memo.computeIfAbsent(n, k -> fib(k - 1) + fib(k - 2));   // modifies the map from inside compute
    }

    public static void main(String[] args) {
        for (Map<Integer, Long> m : List.<Map<Integer, Long>>of(new ConcurrentHashMap<>(), new HashMap<>())) {
            memo = m;
            try {
                System.out.println(m.getClass().getSimpleName() + ": fib(30) = " + fib(30));
            } catch (RuntimeException e) {
                System.out.println(m.getClass().getSimpleName() + ": threw " + e);
            }
        }
        // the fix: build the table bottom-up, outside any compute call
        Map<Integer, Long> table = new ConcurrentHashMap<>(Map.of(0, 0L, 1, 1L));
        for (int n = 2; n <= 30; n++) table.put(n, table.get(n - 1) + table.get(n - 2));
        System.out.println("bottom-up: fib(30) = " + table.get(30));
    }
}
