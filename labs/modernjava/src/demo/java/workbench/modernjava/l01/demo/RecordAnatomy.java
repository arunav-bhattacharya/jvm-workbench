package workbench.modernjava.l01.demo;

import java.util.Arrays;

/** What javac gives a one-line record, seen from the outside. */
public class RecordAnatomy {

    record Point(int x, int y) {}

    public static void main(String[] args) {
        Point a = new Point(3, 4);
        Point b = new Point(3, 4);

        System.out.println("toString:   " + a);
        System.out.println("accessors:  x()=" + a.x() + " y()=" + a.y());
        System.out.println("equals:     " + a.equals(b) + ", same hashCode: " + (a.hashCode() == b.hashCode()));
        System.out.println("==:         " + (a == b) + "   (two objects, each with its own identity)");
        System.out.println("isRecord:   " + Point.class.isRecord());
        System.out.println("components: " + Arrays.toString(Point.class.getRecordComponents()));
        System.out.println("superclass: " + Point.class.getSuperclass().getName());

        synchronized (a) {   // compiles and runs: a record is an ordinary identity object
            System.out.println("locked on a record");
        }
    }
}
