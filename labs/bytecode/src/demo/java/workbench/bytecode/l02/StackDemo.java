package workbench.bytecode.l02;

/** Small methods to read with javap: run the demo once so Gradle compiles it, then javap -c -p. */
public class StackDemo {
    /** How long a lighting fade runs: steps of stepMillis milliseconds each, in whole seconds. */
    static long seconds(long stepMillis, int steps) {
        return stepMillis * steps / 1_000;
    }

    static String describe(String unit, long amount) {
        return amount + " " + unit;
    }

    public static void main(String[] args) {
        long fade = seconds(32, 12_500);
        System.out.println(describe("seconds", fade));   // 400 seconds
    }
}
