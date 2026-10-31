package workbench.generics.l03;

/**
 * Java arrays are covariant: a String[] is an Object[]. So the JVM checks every store into an array
 * at run time, and throws ArrayStoreException when the value does not fit the array's real element type.
 */
public final class ArrayChecks {
    private ArrayChecks() {}

    /**
     * Returns true if {@code array[0] = value} would succeed, false if it would throw
     * ArrayStoreException. Do not catch the exception: ask the array what its element type is.
     * Storing null always works.
     */
    public static boolean canStore(Object[] array, Object value) {
        throw new UnsupportedOperationException("TODO: compare value with the array's runtime component type");
    }

    /**
     * Returns a copy of {@code names} whose runtime type is really Object[], so code that writes
     * any Object into it cannot hit ArrayStoreException. The result must contain the same names.
     */
    public static Object[] widenSafely(String[] names) {
        throw new UnsupportedOperationException("TODO: copy into a new Object[]");
    }
}
