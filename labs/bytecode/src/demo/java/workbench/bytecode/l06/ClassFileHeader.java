package workbench.bytecode.l06;

import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.HexFormat;

/** The first ten bytes of three class files: magic, version and constant pool size. */
public class ClassFileHeader {
    public static void main(String[] args) throws IOException {
        show(ClassFileHeader.class);   // compiled by the labs build with release 21
        show(HeaderMarker.class);      // compiled by kotlinc in the same build (from ClassFileHeader.kt)
        show(Object.class);            // from the JDK you are running
    }

    static void show(Class<?> c) throws IOException {
        byte[] bytes;
        try (InputStream in = c.getResourceAsStream(c.getSimpleName() + ".class")) {
            bytes = in.readAllBytes();
        }
        DataInputStream in = new DataInputStream(new ByteArrayInputStream(bytes));
        int magic = in.readInt();               // u4
        int minor = in.readUnsignedShort();     // u2
        int major = in.readUnsignedShort();     // u2
        int poolCount = in.readUnsignedShort(); // u2: entries are numbered 1 .. poolCount - 1
        System.out.printf("%-34s %s  magic=%X  version=%d.%d (Java %d)  pool entries=%d  size=%d bytes%n",
                c.getName(), HexFormat.ofDelimiter(" ").formatHex(bytes, 0, 10),
                magic, major, minor, major - 44, poolCount - 1, bytes.length);
    }
}
