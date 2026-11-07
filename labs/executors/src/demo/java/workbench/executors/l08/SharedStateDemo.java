package workbench.executors.l08;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.IntStream;

/** Collecting from a parallel stream into shared state, and the stream's own way. */
public class SharedStateDemo {
    public static void main(String[] args) {
        List<Integer> ids = IntStream.range(0, 100_000).boxed().toList();
        Set<String> threads = ConcurrentHashMap.newKeySet();

        List<Integer> shared = new ArrayList<>();
        try {
            ids.parallelStream().forEach(id -> {
                threads.add(Thread.currentThread().getName());
                shared.add(id);                                   // many threads, one ArrayList
            });
            System.out.printf("shared ArrayList:   %,d of %,d ids, in order: %b%n", shared.size(), ids.size(), shared.equals(ids));
        } catch (ArrayIndexOutOfBoundsException e) {
            System.out.println("shared ArrayList:   threw " + e);
        }
        List<Integer> collected = ids.parallelStream().map(id -> id).toList();
        System.out.printf("toList():           %,d of %,d ids, in order: %b%n", collected.size(), ids.size(), collected.equals(ids));

        long[] total = {0};
        ids.parallelStream().forEach(id -> total[0] += id);       // read, add, write from many threads
        long sum = ids.parallelStream().mapToLong(Integer::longValue).sum();
        System.out.printf("shared long[] sum:  %,d%n", total[0]);
        System.out.printf("mapToLong().sum():  %,d%n", sum);

        System.out.println("threads that ran the first stream: " + new TreeSet<>(threads));
    }
}
