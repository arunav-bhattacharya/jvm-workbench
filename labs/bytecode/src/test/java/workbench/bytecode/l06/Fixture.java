package workbench.bytecode.l06;

import java.util.List;
import java.util.function.Supplier;

/** A small class whose constant pool holds nearly every kind of entry. */
public class Fixture implements Comparable<Fixture> {
    sealed interface Instrument permits Card, Wallet {}
    record Card(String pan) implements Instrument {}
    enum Wallet implements Instrument { APPLE_PAY }

    long limitMinor = 9_000_000_000L;                    // Long: two pool indexes
    double fxRate = 1.0842;                              // Double: two pool indexes
    float ratio = 0.25f;                                 // Float
    int bigCount = 1_000_000;                            // Integer
    String currency = "EUR";                             // String
    List<String> pairs = List.of("EURUSD", "GBPUSD");    // InterfaceMethodref
    Supplier<String> label = () -> currency + " " + bigCount;   // InvokeDynamic, MethodHandle, MethodType

    static String describe(Instrument i) {
        return switch (i) {                              // typeSwitch, plus a Dynamic entry for the enum label
            case Card c -> "card " + c.pan();
            case Wallet.APPLE_PAY -> "wallet";
        };
    }

    @Override
    public int compareTo(Fixture o) {
        return Long.compare(limitMinor, o.limitMinor);
    }
}
