package workbench.kotlin.l01.demo;

/**
 * Java twin of InlineDemo.kt. javac cannot inline Kotlin code, so for Java the inline function
 * timed() is an ordinary static method on InlineDemoKt that takes a Function0.
 */
public class InlineDemoJava {
    public static void main(String[] args) {
        // the Java lambda becomes a Function0 object; timed() calls its invoke() like any other method
        long fee = InlineDemoKt.timed("from Java", () -> 12_000L * 3 / 100);
        System.out.println("fee = " + fee);

        // the same idea written in plain Java: a Supplier and a call through it
        long same = timedJava("plain Java", () -> 12_000L * 3 / 100);
        System.out.println("fee = " + same);
    }

    static <T> T timedJava(String label, java.util.function.Supplier<T> block) {
        long start = System.nanoTime();
        try {
            return block.get();
        } finally {
            System.out.println(label + " took " + (System.nanoTime() - start) / 1_000 + " us");
        }
    }
}
