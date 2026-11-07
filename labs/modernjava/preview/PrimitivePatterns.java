// PREVIEW: primitive types in patterns are a preview feature in every JDK from 23 to 27.
// Run from labs/modernjava, on JDK 25:
//   java --enable-preview --source 25 preview/PrimitivePatterns.java
// Without --enable-preview javac says "primitive patterns are a preview feature and are disabled by default".

public class PrimitivePatterns {

    // a switch on an int with type patterns and guards, not only constants
    static String riskBand(int score) {
        return switch (score) {
            case 0 -> "no score";
            case int s when s < 300 -> "high risk (" + s + ")";
            case int s when s < 700 -> "medium risk (" + s + ")";
            case int s -> "low risk (" + s + ")";
        };
    }

    public static void main(String[] args) {
        System.out.println(riskBand(0) + ", " + riskBand(120) + ", " + riskBand(650) + ", " + riskBand(910));

        // instanceof with a primitive type asks "does this value fit exactly?"
        long small = 42L, big = 300L;
        if (small instanceof byte b) System.out.println(small + " fits in a byte: " + b);
        if (!(big instanceof byte)) System.out.println(big + " does not fit in a byte");
    }
}
