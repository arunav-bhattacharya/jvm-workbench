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

    record Money(long minor, String currency) {
        Money {                                                   // compact canonical constructor
            Objects.requireNonNull(currency, "currency");
            if (minor < 0) throw new IllegalArgumentException("negative amount: " + minor);
            currency = currency.toUpperCase(Locale.ROOT);         // reassign the parameter
        }                                                         // fields are assigned here

        Money(long minor) { this(minor, "EUR"); }                 // non-canonical: must delegate

        static Money ofMajor(long major, String ccy) {            // a factory: still goes through it
            return new Money(Math.multiplyExact(major, 100), ccy);
        }
    }

    record Range(int lo, int hi) implements Serializable {
        Range {
            if (lo > hi) throw new IllegalArgumentException("lo > hi: " + lo + " > " + hi);
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println(new Money(1250, "eur"));
        System.out.println(new Money(5));
        System.out.println(Money.ofMajor(3, "usd"));
        try { new Money(-1, "EUR"); } catch (IllegalArgumentException e) { System.out.println("IAE: " + e.getMessage()); }
        try { new Money(1, null); } catch (NullPointerException e) { System.out.println("NPE: " + e.getMessage()); }

        // serialize a valid Range, then swap its two int fields in the byte stream
        byte[] bytes = serialize(new Range(1, 5));
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

    // the stream ends with the int fields (hi, then lo); swapping them turns (1, 5) into (5, 1)
    static void swapLastTwoInts(byte[] b) {
        int n = b.length;
        for (int i = 0; i < 4; i++) {
            byte t = b[n - 8 + i];
            b[n - 8 + i] = b[n - 4 + i];
            b[n - 4 + i] = t;
        }
    }
}
