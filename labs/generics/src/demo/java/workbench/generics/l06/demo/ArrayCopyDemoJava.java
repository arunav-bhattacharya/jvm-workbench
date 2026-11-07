package workbench.generics.l06.demo;

import java.util.Arrays;

/**
 * Java twin of ArrayCopyDemo.kt. Java arrays are covariant, so Object[] already accepts an Integer[].
 * There is no wildcard for arrays. The price: the JVM checks every store at run time.
 */
public class ArrayCopyDemoJava {

    static void copyRow(Object[] from, Object[] to) {
        for (int i = 0; i < from.length; i++) to[i] = from[i];   // each store is checked by the JVM
    }

    public static void main(String[] args) {
        Integer[] amounts = {1_200, 350, 99};
        Object[] row = new Object[3];
        copyRow(amounts, row);
        System.out.println(Arrays.toString(row));

        try {
            copyRow(amounts, new String[3]);     // compiles: a String[] is an Object[]
        } catch (ArrayStoreException e) {
            System.out.println("ArrayStoreException: " + e.getMessage());
        }
    }
}
