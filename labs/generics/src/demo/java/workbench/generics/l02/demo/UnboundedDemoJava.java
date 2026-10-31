package workbench.generics.l02.demo;

/** Java twin of UnboundedDemo.kt. An unbounded T is "some type": only Object's methods are available. */
public class UnboundedDemoJava {

    static <T> String describe(T x) {
        return "value=" + x + ", hash=" + java.util.Objects.hashCode(x);   // Object's methods only
    }

    // Wrong moves. Uncomment ONE at a time, predict the error, then run.
    // static <T> int lengthOf(T x) { return x.length(); }
    // static <T> T bigger(T a, T b) { return a.compareTo(b) >= 0 ? a : b; }

    public static void main(String[] args) {
        System.out.println(describe("EUR"));
        System.out.println(describe(978));
        System.out.println(describe(null));       // any Java T accepts null
    }
}
