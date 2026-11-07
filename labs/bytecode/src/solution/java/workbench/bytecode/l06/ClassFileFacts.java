package workbench.bytecode.l06;

import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Set;
import java.util.TreeSet;

public final class ClassFileFacts {
    private ClassFileFacts() {}

    public record Header(int minor, int major, int constantPoolCount) {}

    public static Header header(byte[] classFile) {
        try {
            DataInputStream in = open(classFile);
            return readHeader(in);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    public static int javaVersion(int major) {
        if (major < 49) throw new IllegalArgumentException("major " + major + " is older than Java 5");
        return major - 44;                         // 49 = Java 5 ... 65 = Java 21 ... 69 = Java 25
    }

    public static String thisClass(byte[] classFile) {
        try {
            DataInputStream in = open(classFile);
            Pool pool = readPool(in, readHeader(in).constantPoolCount());
            in.readUnsignedShort();                // access_flags
            int thisIndex = in.readUnsignedShort();
            return pool.utf8[pool.classNameIndex[thisIndex]];
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    public static Set<String> referencedClasses(byte[] classFile) {
        try {
            DataInputStream in = open(classFile);
            Pool pool = readPool(in, readHeader(in).constantPoolCount());
            Set<String> names = new TreeSet<>();
            for (int i = 1; i < pool.utf8.length; i++) {
                if (pool.classNameIndex[i] != 0) names.add(pool.utf8[pool.classNameIndex[i]]);
            }
            return names;
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    // ---- the parts every method shares ----

    private record Pool(String[] utf8, int[] classNameIndex) {}

    private static DataInputStream open(byte[] classFile) {
        return new DataInputStream(new ByteArrayInputStream(classFile));
    }

    private static Header readHeader(DataInputStream in) throws IOException {
        int magic = in.readInt();
        if (magic != 0xCAFEBABE) {
            throw new IllegalArgumentException("not a class file: magic is 0x" + Integer.toHexString(magic));
        }
        int minor = in.readUnsignedShort();
        int major = in.readUnsignedShort();
        return new Header(minor, major, in.readUnsignedShort());
    }

    private static Pool readPool(DataInputStream in, int count) throws IOException {
        String[] utf8 = new String[count];
        int[] classNameIndex = new int[count];
        for (int i = 1; i < count; i++) {                  // index 0 is never used
            int tag = in.readUnsignedByte();
            switch (tag) {
                case 1 -> utf8[i] = in.readUTF();         // u2 length + modified UTF-8, as DataInput defines it
                case 7 -> classNameIndex[i] = in.readUnsignedShort();
                case 8, 16, 19, 20 -> in.skipBytes(2);
                case 15 -> in.skipBytes(3);
                case 3, 4, 9, 10, 11, 12, 17, 18 -> in.skipBytes(4);
                case 5, 6 -> {
                    in.skipBytes(8);
                    i++;                                   // long and double take two pool indexes
                }
                default -> throw new IllegalArgumentException("unknown constant pool tag " + tag + " at index " + i);
            }
        }
        return new Pool(utf8, classNameIndex);
    }
}
