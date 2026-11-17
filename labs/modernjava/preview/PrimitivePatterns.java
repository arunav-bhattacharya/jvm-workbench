// PREVIEW: primitive types in patterns are a preview feature in every JDK from 23 to 27.
// Run from labs/modernjava, on JDK 25:
//   java --enable-preview --source 25 preview/PrimitivePatterns.java
// Without --enable-preview javac says "primitive patterns are a preview feature and are disabled by default".

public class PrimitivePatterns {

    // a switch on an int with type patterns and guards, not only constants
    static String length(int pages) {
        return switch (pages) {
            case 0 -> "no pages";
            case int p when p < 100 -> "short (" + p + " pages)";
            case int p when p < 400 -> "medium (" + p + " pages)";
            case int p -> "long (" + p + " pages)";
        };
    }

    public static void main(String[] args) {
        System.out.println(length(0) + ", " + length(64) + ", " + length(288) + ", " + length(1_216));

        // instanceof with a primitive type asks "does this value fit exactly?"
        long small = 42L, big = 300L;
        if (small instanceof byte b) System.out.println(small + " fits in a byte: " + b);
        if (!(big instanceof byte)) System.out.println(big + " does not fit in a byte");
    }
}
