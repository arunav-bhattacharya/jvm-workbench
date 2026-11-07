package workbench.performance.l02;

import java.io.DataInputStream;
import java.io.IOException;
import java.io.InputStream;

/**
 * Reads a compiled class file and returns the bytecode length of one method: the same number
 * PrintCompilation prints as "(N bytes)" and that C2 compares with MaxInlineSize.
 * A tiny class-file reader, so the test needs no bytecode library.
 */
final class BytecodeSize {
    private BytecodeSize() { }

    static int of(Class<?> type, String methodName, String descriptor) throws IOException {
        String resource = type.getSimpleName() + ".class";
        try (InputStream raw = type.getResourceAsStream(resource);
             DataInputStream in = new DataInputStream(raw)) {
            if (in.readInt() != 0xCAFEBABE) throw new IOException("not a class file");
            in.readUnsignedShort();                       // minor version
            in.readUnsignedShort();                       // major version
            int count = in.readUnsignedShort();
            String[] utf8 = new String[count];
            for (int i = 1; i < count; i++) {             // the constant pool
                int tag = in.readUnsignedByte();
                switch (tag) {
                    case 1 -> utf8[i] = in.readUTF();
                    case 3, 4 -> in.skipNBytes(4);
                    case 5, 6 -> { in.skipNBytes(8); i++; }      // long and double take two slots
                    case 7, 8, 16, 19, 20 -> in.skipNBytes(2);
                    case 9, 10, 11, 12, 17, 18 -> in.skipNBytes(4);
                    case 15 -> in.skipNBytes(3);
                    default -> throw new IOException("unknown constant pool tag " + tag);
                }
            }
            in.skipNBytes(6);                             // access flags, this class, super class
            in.skipNBytes(2L * in.readUnsignedShort());   // interfaces
            int fields = in.readUnsignedShort();
            for (int f = 0; f < fields; f++) {
                in.skipNBytes(6);
                skipAttributes(in);
            }
            int methods = in.readUnsignedShort();
            for (int m = 0; m < methods; m++) {
                in.readUnsignedShort();                   // access flags
                String name = utf8[in.readUnsignedShort()];
                String desc = utf8[in.readUnsignedShort()];
                int attrs = in.readUnsignedShort();
                for (int a = 0; a < attrs; a++) {
                    String attrName = utf8[in.readUnsignedShort()];
                    int length = in.readInt();
                    if (attrName.equals("Code") && name.equals(methodName) && desc.equals(descriptor)) {
                        in.readUnsignedShort();           // max stack
                        in.readUnsignedShort();           // max locals
                        return in.readInt();              // code length: the bytecode size
                    }
                    in.skipNBytes(length);
                }
            }
        }
        throw new IllegalArgumentException("no method " + methodName + descriptor + " in " + type.getName());
    }

    private static void skipAttributes(DataInputStream in) throws IOException {
        int attrs = in.readUnsignedShort();
        for (int a = 0; a < attrs; a++) {
            in.readUnsignedShort();
            in.skipNBytes(in.readInt() & 0xFFFFFFFFL);
        }
    }
}
