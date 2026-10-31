package workbench.jmm.l04;

/** Where final fields come from in Java. Run javap on the compiled classes to see them. */
public class FinalFieldsDemo {
    // a record's components become private final fields
    record Quote(String scheme, long feeCents) {}

    // for contrast: plain, non-final fields
    static final class MutableQuote {
        String scheme;
        long feeCents;
    }

    public static void main(String[] args) {
        Quote q = new Quote("VISA", 120);
        MutableQuote m = new MutableQuote();
        m.scheme = "MC";
        m.feeCents = 135;
        System.out.println(q + " and a mutable quote for " + m.scheme);
    }
}
