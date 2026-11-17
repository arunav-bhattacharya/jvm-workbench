package workbench.performance.l04;

import org.openjdk.jol.info.ClassLayout;

/** Prints the real field layout of four classes with JOL: where each field sits, in bytes. */
public class LayoutDemo {
    static final class Adjacent {
        volatile long parsed;
        volatile long written;
    }

    static final class PaddedInOneClass {         // padding fields between the counters
        volatile long parsed;
        long p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16;
        volatile long written;
    }

    static class ParsedField { volatile long parsed; }   // superclass fields are laid out first
    static class Pad1 extends ParsedField { long p1, p2, p3, p4, p5, p6, p7, p8; }
    static class WrittenField extends Pad1 { volatile long written; }
    static final class Padded extends WrittenField { long q1, q2, q3, q4, q5, q6, q7, q8; }

    public static void main(String[] args) throws Exception {
        print(Adjacent.class);
        print(PaddedInOneClass.class);
        print(Padded.class);
        // the cell behind LongAdder: the JDK pads it with @Contended
        print(Class.forName("java.util.concurrent.atomic.Striped64$Cell"));
    }

    static void print(Class<?> type) {
        ClassLayout layout = ClassLayout.parseClass(type);
        System.out.println(type.getSimpleName() + ": " + layout.instanceSize() + " bytes");
        layout.fields().stream()
              .filter(f -> f.name().equals("parsed") || f.name().equals("written") || f.name().equals("value"))
              .forEach(f -> System.out.printf("  %-7s at offset %3d%n", f.name(), f.offset()));
    }
}
