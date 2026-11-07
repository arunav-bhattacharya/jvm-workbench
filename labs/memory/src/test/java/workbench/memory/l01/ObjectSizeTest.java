package workbench.memory.l01;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.openjdk.jol.info.ClassLayout;
import org.openjdk.jol.vm.VM;
import workbench.memory.l01.ObjectSize.Vm;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static workbench.memory.l01.ObjectSize.Vm.ALIGN_16;
import static workbench.memory.l01.ObjectSize.Vm.COMPACT_HEADERS;
import static workbench.memory.l01.ObjectSize.Vm.DEFAULT;
import static workbench.memory.l01.ObjectSize.Vm.NO_COMPRESSED_OOPS;

class ObjectSizeTest {

    @BeforeAll
    static void letJolReadRecords() {
        // JOL cannot read record field offsets on JDK 21 without this; it must be set before JOL starts
        System.setProperty("jol.magicFieldOffset", "true");
    }

    @Test
    @DisplayName("alignUp rounds up to the next multiple of the alignment")
    void alignUp() {
        assertThat(ObjectSize.alignUp(13, 8)).isEqualTo(16);
        assertThat(ObjectSize.alignUp(16, 8)).isEqualTo(16);
        assertThat(ObjectSize.alignUp(17, 8)).isEqualTo(24);
        assertThat(ObjectSize.alignUp(19, 16)).isEqualTo(32);
        assertThat(ObjectSize.alignUp(0, 8)).isEqualTo(0);
    }

    @Test
    @DisplayName("fieldBytes gives primitive widths, and one reference for any object or array type")
    void fieldBytes() {
        assertThat(ObjectSize.fieldBytes(DEFAULT, long.class)).isEqualTo(8);
        assertThat(ObjectSize.fieldBytes(DEFAULT, double.class)).isEqualTo(8);
        assertThat(ObjectSize.fieldBytes(DEFAULT, int.class)).isEqualTo(4);
        assertThat(ObjectSize.fieldBytes(DEFAULT, float.class)).isEqualTo(4);
        assertThat(ObjectSize.fieldBytes(DEFAULT, char.class)).isEqualTo(2);
        assertThat(ObjectSize.fieldBytes(DEFAULT, short.class)).isEqualTo(2);
        assertThat(ObjectSize.fieldBytes(DEFAULT, byte.class)).isEqualTo(1);
        assertThat(ObjectSize.fieldBytes(DEFAULT, boolean.class)).isEqualTo(1);
        assertThat(ObjectSize.fieldBytes(DEFAULT, String.class)).as("a String field is a reference").isEqualTo(4);
        assertThat(ObjectSize.fieldBytes(DEFAULT, long[].class)).as("an array field is a reference too").isEqualTo(4);
        assertThat(ObjectSize.fieldBytes(NO_COMPRESSED_OOPS, String.class)).isEqualTo(8);
    }

    @Test
    @DisplayName("by default an Object and an Integer take 16 bytes, a Long 24")
    void boxes() {
        assertThat(ObjectSize.instanceSize(DEFAULT, Object.class)).as("Object").isEqualTo(16);
        assertThat(ObjectSize.instanceSize(DEFAULT, Integer.class)).as("Integer").isEqualTo(16);
        assertThat(ObjectSize.instanceSize(DEFAULT, Long.class)).as("Long").isEqualTo(24);
    }

    @Test
    @DisplayName("Payment is 40 bytes by default, 48 without compressed oops or with 16-byte alignment, 32 with compact headers")
    void paymentInEveryMode() {
        // the first three are JOL measurements on JDK 21; the last is JOL's simulation of compact headers
        assertThat(ObjectSize.instanceSize(DEFAULT, Samples.Payment.class)).isEqualTo(40);
        assertThat(ObjectSize.instanceSize(NO_COMPRESSED_OOPS, Samples.Payment.class)).isEqualTo(48);
        assertThat(ObjectSize.instanceSize(ALIGN_16, Samples.Payment.class)).isEqualTo(48);
        assertThat(ObjectSize.instanceSize(COMPACT_HEADERS, Samples.Payment.class)).isEqualTo(32);
    }

    @Test
    @DisplayName("compact headers save 8 bytes on a Long and nothing on an Integer")
    void compactHeadersAndPadding() {
        assertThat(ObjectSize.instanceSize(COMPACT_HEADERS, Long.class)).isEqualTo(16);
        assertThat(ObjectSize.instanceSize(COMPACT_HEADERS, Integer.class)).isEqualTo(16);
    }

    @Test
    @DisplayName("superclass fields count, static fields don't")
    void superclassAndStatics() {
        // CardPayment adds 6 bytes of fields to Payment, and they fit in Payment's 6 bytes of padding
        assertThat(ObjectSize.instanceSize(DEFAULT, Samples.CardPayment.class)).isEqualTo(40);
        assertThat(ObjectSize.instanceSize(NO_COMPRESSED_OOPS, Samples.CardPayment.class)).isEqualTo(56);
        assertThat(ObjectSize.instanceSize(DEFAULT, Samples.FeeRule.class)).isEqualTo(16);
    }

    @Test
    @DisplayName("arrays: header, a 4-byte length, the elements, then padding")
    void arrays() {
        assertThat(ObjectSize.arraySize(DEFAULT, byte.class, 3)).isEqualTo(24);
        assertThat(ObjectSize.arraySize(DEFAULT, int.class, 1000)).isEqualTo(4_016);
        assertThat(ObjectSize.arraySize(DEFAULT, Object.class, 2)).isEqualTo(24);
        assertThat(ObjectSize.arraySize(NO_COMPRESSED_OOPS, Object.class, 2)).isEqualTo(32);
        assertThat(ObjectSize.arraySize(ALIGN_16, byte.class, 3)).isEqualTo(32);
    }

    @Test
    @DisplayName("your predictions match JOL in the JVM that runs these tests")
    void matchesJol() {
        Vm here = new Vm(VM.current().objectHeaderSize(), (int) VM.current().sizeOfField("oop"), VM.current().objectAlignment());
        for (Class<?> c : List.of(Object.class, Integer.class, Long.class, String.class, Samples.Payment.class,
                Samples.CardPayment.class, Samples.LedgerEntry.class, Samples.FeeRule.class, Samples.Money.class)) {
            assertThat(ObjectSize.instanceSize(here, c)).as(c.getSimpleName()).isEqualTo(ClassLayout.parseClass(c).instanceSize());
        }
        assertThat(ObjectSize.arraySize(here, byte.class, 3)).as("byte[3]").isEqualTo(ClassLayout.parseInstance(new byte[3]).instanceSize());
        assertThat(ObjectSize.arraySize(here, long.class, 5)).as("long[5]").isEqualTo(ClassLayout.parseInstance(new long[5]).instanceSize());
        assertThat(ObjectSize.arraySize(here, String.class, 7)).as("String[7]").isEqualTo(ClassLayout.parseInstance(new String[7]).instanceSize());
    }
}
