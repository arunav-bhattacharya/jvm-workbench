package workbench.kotlin.l01.demo;

/**
 * Java twin of PublishedApiDemo.kt. `internal` is a Kotlin rule that javac does not know about.
 * In the bytecode nextTraceId() is public, so Java can call it, and traced() is an ordinary method.
 */
public class PublishedApiDemoJava {
    public static void main(String[] args) {
        long grams = PublishedApiDemoKt.traced("weigh parcel job_7", () -> 1_999L);
        System.out.println("parcel weighs " + PublishedApiDemoKt.getAsKilos(grams));
        System.out.println("Java can call the internal helper too: " + PublishedApiDemoKt.nextTraceId());
    }
}
