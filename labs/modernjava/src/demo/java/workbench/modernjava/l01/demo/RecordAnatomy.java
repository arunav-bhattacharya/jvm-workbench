package workbench.modernjava.l01.demo;

import java.util.Arrays;

/** What javac gives a one-line record, seen from the outside. */
public class RecordAnatomy {

    // Naive: written by hand. The shelf was added later, and not to every method.
    static final class OldShelfmark {
        private final String section;
        private final int shelf;                                  // added later

        OldShelfmark(String section, int shelf) { this.section = section; this.shelf = shelf; }
        String section() { return section; }
        int shelf() { return shelf; }

        @Override public boolean equals(Object o) {
            return o instanceof OldShelfmark s && s.section.equals(section);   // nobody updated this
        }
        @Override public int hashCode() { return section.hashCode(); }
        @Override public String toString() { return "OldShelfmark[section=" + section + "]"; }
    }

    record Shelfmark(String section, int shelf) {}

    public static void main(String[] args) {
        OldShelfmark old12 = new OldShelfmark("FIC", 12), old40 = new OldShelfmark("FIC", 40);
        System.out.println("by hand:    " + old12 + " equals " + old40 + ": " + old12.equals(old40));

        Shelfmark a = new Shelfmark("FIC", 12);
        Shelfmark b = new Shelfmark("FIC", 12);

        System.out.println("toString:   " + a);
        System.out.println("accessors:  section()=" + a.section() + " shelf()=" + a.shelf());
        System.out.println("equals:     " + a.equals(b) + ", same hashCode: " + (a.hashCode() == b.hashCode()));
        System.out.println("==:         " + (a == b) + "   (two objects, each with its own identity)");
        System.out.println("isRecord:   " + Shelfmark.class.isRecord());
        System.out.println("components: " + Arrays.toString(Shelfmark.class.getRecordComponents()));
        System.out.println("superclass: " + Shelfmark.class.getSuperclass().getName());

        synchronized (a) {   // compiles and runs: a record is an ordinary identity object
            System.out.println("locked on a record");
        }
    }
}
