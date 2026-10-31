package workbench.generics.l03;

import java.util.Arrays;

public final class ArrayChecks {
    private ArrayChecks() {}

    public static boolean canStore(Object[] array, Object value) {
        if (value == null) return true;                       // null fits any reference array
        // an array remembers its element type at run time (generics do not): ask it
        return array.getClass().getComponentType().isInstance(value);
    }

    public static Object[] widenSafely(String[] names) {
        // the third argument picks the runtime type of the new array: a real Object[]
        return Arrays.copyOf(names, names.length, Object[].class);
    }
}
