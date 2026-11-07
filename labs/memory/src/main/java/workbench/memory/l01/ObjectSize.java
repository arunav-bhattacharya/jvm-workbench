package workbench.memory.l01;

/**
 * Predicts how many bytes one object or one array takes on a 64-bit HotSpot JVM.
 *
 * <p>Three numbers decide it, and {@link Vm} holds them: the header size, the size of a reference
 * field, and the alignment every object is padded to. Write the four methods below. The tests check
 * your answers against numbers JOL measured, and then against JOL in the JVM that runs the tests.
 */
public final class ObjectSize {
    private ObjectSize() {}

    /** The three numbers that decide object sizes. */
    public record Vm(int headerBytes, int referenceBytes, int alignment) {
        /** JDK 21 to 26 with a heap under about 32 GB: 8-byte mark word + 4-byte class pointer, 4-byte references. */
        public static final Vm DEFAULT = new Vm(12, 4, 8);
        /** {@code -XX:-UseCompressedOops}, or {@code -Xmx32g} and up: references grow to 8 bytes. */
        public static final Vm NO_COMPRESSED_OOPS = new Vm(12, 8, 8);
        /** {@code -XX:+UseCompactObjectHeaders} (opt-in on JDK 25, the default on JDK 27): an 8-byte header. */
        public static final Vm COMPACT_HEADERS = new Vm(8, 4, 8);
        /** {@code -XX:ObjectAlignmentInBytes=16}: compressed oops reach 64 GB, every object pads to 16. */
        public static final Vm ALIGN_16 = new Vm(12, 4, 16);
    }

    /** Rounds {@code size} up to the next multiple of {@code alignment}, which is a power of two. */
    public static long alignUp(long size, int alignment) {
        throw new UnsupportedOperationException("TODO: round size up to a multiple of alignment");
    }

    /**
     * Bytes one field of this type takes: boolean and byte 1, char and short 2, int and float 4,
     * long and double 8. Every reference type (String, arrays, your own classes) is {@code vm.referenceBytes()}.
     */
    public static int fieldBytes(Vm vm, Class<?> type) {
        throw new UnsupportedOperationException("TODO: primitive widths, or vm.referenceBytes() for references");
    }

    /**
     * Shallow size of one instance of {@code type}: the header, plus every instance field declared by
     * the class and all its superclasses (skip static fields), rounded up to the alignment.
     * Use {@code getDeclaredFields()} and {@code getSuperclass()}.
     */
    public static long instanceSize(Vm vm, Class<?> type) {
        throw new UnsupportedOperationException("TODO: header + instance fields of the class and its superclasses, aligned");
    }

    /** Size of an array: the header, a 4-byte length field, then {@code length} elements, rounded up. */
    public static long arraySize(Vm vm, Class<?> componentType, int length) {
        throw new UnsupportedOperationException("TODO: header + 4 + length * element size, aligned");
    }
}
