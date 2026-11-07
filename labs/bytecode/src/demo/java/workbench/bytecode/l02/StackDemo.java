package workbench.bytecode.l02;

/** Small methods to read with javap: run the demo once so Gradle compiles it, then javap -c -p. */
public class StackDemo {
    /** Card fee in minor units: amount times basis points, divided by 10,000. */
    static long feeMinor(long amountMinor, int bps) {
        return amountMinor * bps / 10_000;
    }

    static String describe(String currency, long amountMinor) {
        return amountMinor + " " + currency;
    }

    public static void main(String[] args) {
        long fee = feeMinor(125_000, 290);
        System.out.println(describe("EUR", fee));   // 3625 EUR
    }
}
