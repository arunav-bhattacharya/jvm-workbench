package workbench.modernjava.l01.demo;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.Serializable;
import java.util.Locale;
import java.util.Objects;

/** Every way of making a record goes through its canonical constructor, even deserialization. */
public class CompactConstructorDemo {

    record Shelfmark(String section, int shelf) {
        Shelfmark {                                               // compact canonical constructor
            Objects.requireNonNull(section, "section");
            if (shelf < 1) throw new IllegalArgumentException("shelf must be 1 or more: " + shelf);
            section = section.toUpperCase(Locale.ROOT);           // reassign the parameter
        }                                                         // fields are assigned here

        Shelfmark(String section) { this(section, 1); }          // non-canonical: must delegate

        static Shelfmark parse(String label) {                   // a factory: still goes through it
            String[] parts = label.trim().split(" ");
            return new Shelfmark(parts[0], Integer.parseInt(parts[1]));
        }
    }

    // a request to photocopy pages first to last of a book
    record PageRange(int first, int last) implements Serializable {
        PageRange {
            if (first > last) throw new IllegalArgumentException("first > last: " + first + " > " + last);
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println(new Shelfmark("fic", 12));
        System.out.println(new Shelfmark("bio"));
        System.out.println(Shelfmark.parse("ref 7"));
        try { new Shelfmark("FIC", 0); } catch (IllegalArgumentException e) { System.out.println("IAE: " + e.getMessage()); }
        try { new Shelfmark(null, 1); } catch (NullPointerException e) { System.out.println("NPE: " + e.getMessage()); }

        // serialize a valid PageRange, then swap its two int fields in the byte stream
        byte[] bytes = serialize(new PageRange(1, 5));
        swapLastTwoInts(bytes);
        try (var in = new ObjectInputStream(new ByteArrayInputStream(bytes))) {
            System.out.println("tampered stream gave: " + in.readObject());
        } catch (java.io.InvalidObjectException e) {
            System.out.println("tampered stream rejected: " + e.getMessage());
        }
    }

    static byte[] serialize(Object o) throws Exception {
        var buf = new ByteArrayOutputStream();
        try (var out = new ObjectOutputStream(buf)) { out.writeObject(o); }
        return buf.toByteArray();
    }

    // the stream ends with the two int fields; swapping them turns (1, 5) into (5, 1)
    static void swapLastTwoInts(byte[] b) {
        int n = b.length;
        for (int i = 0; i < 4; i++) {
            byte t = b[n - 8 + i];
            b[n - 8 + i] = b[n - 4 + i];
            b[n - 4 + i] = t;
        }
    }
}
