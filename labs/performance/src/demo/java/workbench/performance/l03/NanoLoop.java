package workbench.performance.l03;

/**
 * The benchmark everyone writes first: a loop timed with System.nanoTime().
 * Round by round it measures the same thing, twice: once with the result thrown away,
 * once with the result added to a sum that gets printed.
 */
public class NanoLoop {
    public static void main(String[] args) {
        double x = 2.0;
        for (int round = 1; round <= 5; round++) {
            long t0 = System.nanoTime();
            for (int i = 0; i < 100_000_000; i++) {
                Math.sqrt(x);                      // result discarded
            }
            long t1 = System.nanoTime();

            double sum = 0;
            for (int i = 0; i < 100_000_000; i++) {
                sum += Math.sqrt(x + i);           // result used
            }
            long t2 = System.nanoTime();

            System.out.printf("round %d: discarded %.4f ns/op, used %.4f ns/op (sum %.1f)%n",
                    round, (t1 - t0) / 1e8, (t2 - t1) / 1e8, sum);
        }
    }
}
