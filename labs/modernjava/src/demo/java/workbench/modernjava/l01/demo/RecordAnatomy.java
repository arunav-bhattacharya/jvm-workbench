package workbench.modernjava.l01.demo;

import java.util.Arrays;

/** What javac gives a one-line record, seen from the outside. */
public class RecordAnatomy {

    record Shelfmark(String section, int shelf) {}

    public static void main(String[] args) {
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
