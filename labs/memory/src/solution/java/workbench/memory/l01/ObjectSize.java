package workbench.memory.l01;

import java.lang.reflect.Field;
import java.lang.reflect.Modifier;

public final class ObjectSize {
    private ObjectSize() {}

    public record Vm(int headerBytes, int referenceBytes, int alignment) {
        public static final Vm DEFAULT = new Vm(12, 4, 8);
        public static final Vm NO_COMPRESSED_OOPS = new Vm(12, 8, 8);
        public static final Vm COMPACT_HEADERS = new Vm(8, 4, 8);
        public static final Vm ALIGN_16 = new Vm(12, 4, 16);
    }

    public static long alignUp(long size, int alignment) {
        // alignment is a power of two, so "round up" is: add alignment - 1, then clear the low bits
        return (size + alignment - 1) & -(long) alignment;
    }

    public static int fieldBytes(Vm vm, Class<?> type) {
        if (type == long.class || type == double.class) return 8;
        if (type == int.class || type == float.class) return 4;
        if (type == char.class || type == short.class) return 2;
        if (type == byte.class || type == boolean.class) return 1;
        return vm.referenceBytes();                       // String, arrays, boxes, your classes: one reference
    }

    public static long instanceSize(Vm vm, Class<?> type) {
        long size = vm.headerBytes();
        for (Class<?> c = type; c != null; c = c.getSuperclass()) {      // superclass fields live in the object too
            for (Field f : c.getDeclaredFields()) {
                if (Modifier.isStatic(f.getModifiers())) continue;       // statics live with the class, not the object
                size += fieldBytes(vm, f.getType());
            }
        }
        // the VM may leave small gaps between fields; for these classes they disappear in the final padding
        return alignUp(size, vm.alignment());
    }

    public static long arraySize(Vm vm, Class<?> componentType, int length) {
        long size = vm.headerBytes() + 4L + (long) length * fieldBytes(vm, componentType);   // 4 = the length field
        return alignUp(size, vm.alignment());
    }
}
