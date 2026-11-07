package workbench.kotlin.l01.demo;

/**
 * Java twin of PublishedApiDemo.kt. `internal` is a Kotlin rule that javac does not know about.
 * In the bytecode nextTraceId() is public, so Java can call it, and traced() is an ordinary method.
 */
public class PublishedApiDemoJava {
    public static void main(String[] args) {
        long refunded = PublishedApiDemoKt.traced("refund pay_7", () -> 1_999L);
        System.out.println("refunded " + PublishedApiDemoKt.getAsEuros(refunded));
        System.out.println("Java can call the internal helper too: " + PublishedApiDemoKt.nextTraceId());
    }
}
