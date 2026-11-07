package workbench.performance.l04;

import org.openjdk.jol.info.ClassLayout;

/** Prints the real field layout of four classes with JOL: where each field sits, in bytes. */
public class LayoutDemo {
    static final class Adjacent {
        volatile long card;
        volatile long sepa;
    }

    static final class PaddedInOneClass {         // padding fields between the counters
        volatile long card;
        long p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16;
        volatile long sepa;
    }

    static class CardField { volatile long card; }   // superclass fields are laid out first
    static class Pad1 extends CardField { long p1, p2, p3, p4, p5, p6, p7, p8; }
    static class SepaField extends Pad1 { volatile long sepa; }
    static final class Padded extends SepaField { long q1, q2, q3, q4, q5, q6, q7, q8; }

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
              .filter(f -> f.name().equals("card") || f.name().equals("sepa") || f.name().equals("value"))
              .forEach(f -> System.out.printf("  %-5s at offset %3d%n", f.name(), f.offset()));
    }
}
