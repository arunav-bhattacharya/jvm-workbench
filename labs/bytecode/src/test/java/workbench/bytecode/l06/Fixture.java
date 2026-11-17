package workbench.bytecode.l06;

import java.util.List;
import java.util.function.Supplier;

/** A small class whose constant pool holds nearly every kind of entry. */
public class Fixture implements Comparable<Fixture> {
    sealed interface Seat permits Stalls, Box {}
    record Stalls(String row) implements Seat {}
    enum Box implements Seat { ROYAL }

    long runMillis = 9_000_000_000L;                     // Long: two pool indexes
    double dimmer = 0.8642;                              // Double: two pool indexes
    float ratio = 0.25f;                                 // Float
    int bigCount = 1_000_000;                            // Integer
    String venue = "Riverside";                          // String
    List<String> acts = List.of("Act 1", "Act 2");       // InterfaceMethodref
    Supplier<String> label = () -> venue + " " + bigCount;   // InvokeDynamic, MethodHandle, MethodType

    static String describe(Seat s) {
        return switch (s) {                              // typeSwitch, plus a Dynamic entry for the enum label
            case Stalls st -> "stalls row " + st.row();
            case Box.ROYAL -> "royal box";
        };
    }

    @Override
    public int compareTo(Fixture o) {
        return Long.compare(runMillis, o.runMillis);
    }
}
