package workbench.functional.l08;

import java.util.stream.LongStream;

/** Java has no tailrec, and the JVM doesn't remove tail calls: a call in tail position still uses a frame. */
public class RecursionJava {
    static long sumNaive(long n) { return n == 0 ? 0 : n + sumNaive(n - 1); }

    static long sumTail(long n, long acc) { return n == 0 ? acc : sumTail(n - 1, acc + n); }   // tail position, still a call

    static long sumLoop(long n) {                                                               // what tailrec writes for you
        long acc = 0;
        while (n > 0) { acc += n; n--; }
        return acc;
    }

    public static void main(String[] args) {
        try {
            System.out.println("sumTail(1,000,000) = " + sumTail(1_000_000, 0));
        } catch (StackOverflowError e) {
            System.out.println("sumTail(1,000,000): StackOverflowError");
        }
        try {
            System.out.println("sumNaive(1,000,000) = " + sumNaive(1_000_000));
        } catch (StackOverflowError e) {
            System.out.println("sumNaive(1,000,000): StackOverflowError");
        }
        System.out.println("loop = " + sumLoop(1_000_000));
        System.out.println("LongStream.sum = " + LongStream.rangeClosed(1, 1_000_000).sum());
    }
}
