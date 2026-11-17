package workbench.events.l01.demo.values;

import java.lang.reflect.Field;
import java.math.BigDecimal;
import java.util.List;

public class ValuesDemoJava {
    record ParcelId(String value) {
        ParcelId {
            if (!value.matches("PP-[0-9]{4,12}")) throw new IllegalArgumentException("invalid parcel id: '" + value + "'");
        }
        @Override public String toString() { return value; }
    }

    record Weight(long grams) {
        Weight {
            if (grams < 0) throw new IllegalArgumentException("weight must not be negative: " + grams);
        }
        @Override public String toString() { return BigDecimal.valueOf(grams, 3).stripTrailingZeros().toPlainString() + " kg"; }
    }

    record ParcelCollected(ParcelId parcelId, Weight weight) {}

    /** A parcel described with raw types: nothing stops a caller from swapping the two longs. */
    record RawParcel(String parcelId, long grams, long centimetres) {}

    public static void main(String[] args) {
        System.out.println(new ParcelCollected(new ParcelId("PP-7781"), new Weight(2_500)));
        System.out.println(new RawParcel("PP-7781", 40, 2_500));     // swapped: a 40-gram parcel, 25 metres long

        // Step 2: uncomment. The arguments are in the wrong order.
        // System.out.println(new ParcelCollected(new Weight(2_500), new ParcelId("PP-7781")));

        List<Runnable> attempts = List.of(() -> new ParcelId("7781"), () -> new Weight(-500));
        for (Runnable attempt : attempts) {
            try {
                attempt.run();
            } catch (IllegalArgumentException e) {
                System.out.println("refused: " + e.getMessage());
            }
        }

        // What the JVM stores: each field points at a separate wrapper object on the heap
        for (Field f : ParcelCollected.class.getDeclaredFields()) System.out.println("field " + f.getName() + ": " + f.getType().getName());
    }
}
