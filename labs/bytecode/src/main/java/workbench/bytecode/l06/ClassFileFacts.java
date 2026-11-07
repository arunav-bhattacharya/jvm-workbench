package workbench.bytecode.l06;

import java.util.Set;

/**
 * Read facts straight out of class-file bytes, the way the ClassFile API's {@code ClassModel}
 * (JDK 24+) does underneath. Use {@link java.io.DataInputStream}: it reads big-endian
 * {@code u2}/{@code u4} values, and its {@code readUTF()} reads exactly the class file's
 * Utf8 entry format.
 *
 * <pre>
 * ClassFile {
 *     u4 magic;                       0xCAFEBABE
 *     u2 minor_version;
 *     u2 major_version;
 *     u2 constant_pool_count;         entries are numbered 1 .. count - 1
 *     cp_info constant_pool[count-1]; each starts with a u1 tag (table below)
 *     u2 access_flags;
 *     u2 this_class;                  index of a Class entry
 *     u2 super_class;
 *     ...                             interfaces, fields, methods, attributes
 * }
 *
 * tag  entry               bytes after the tag
 *  1   Utf8                u2 length, then that many bytes   (DataInputStream.readUTF)
 *  3   Integer             4
 *  4   Float               4
 *  5   Long                8, and it uses TWO pool indexes: skip the next index
 *  6   Double              8, and it uses TWO pool indexes: skip the next index
 *  7   Class               u2 name_index (a Utf8 entry)
 *  8   String              2
 *  9   Fieldref            4
 * 10   Methodref           4
 * 11   InterfaceMethodref  4
 * 12   NameAndType         4
 * 15   MethodHandle        3
 * 16   MethodType          2
 * 17   Dynamic             4
 * 18   InvokeDynamic       4
 * 19   Module              2
 * 20   Package             2
 * </pre>
 */
public final class ClassFileFacts {
    private ClassFileFacts() {}

    /** The first four header fields. */
    public record Header(int minor, int major, int constantPoolCount) {}

    /**
     * Reads magic, minor, major and constant_pool_count. Throws {@link IllegalArgumentException}
     * with a message containing "magic" if the bytes don't start with 0xCAFEBABE.
     */
    public static Header header(byte[] classFile) {
        throw new UnsupportedOperationException("TODO: read u4 magic, u2 minor, u2 major, u2 count");
    }

    /**
     * The Java version that writes {@code major}: 52 is Java 8, 65 is Java 21, 69 is Java 25.
     * Throws {@link IllegalArgumentException} for anything older than Java 5 (major 49).
     */
    public static int javaVersion(int major) {
        throw new UnsupportedOperationException("TODO: from Java 5 on, the version is major - 44");
    }

    /** The class's own name in internal form, e.g. {@code "workbench/bytecode/l06/Fixture"}. */
    public static String thisClass(byte[] classFile) {
        throw new UnsupportedOperationException("TODO: walk the whole pool, then read access_flags and this_class");
    }

    /** The names of all Class entries in the constant pool: every class this class mentions, itself included. */
    public static Set<String> referencedClasses(byte[] classFile) {
        throw new UnsupportedOperationException("TODO: walk the pool, remember Utf8 strings and Class name indexes");
    }
}
