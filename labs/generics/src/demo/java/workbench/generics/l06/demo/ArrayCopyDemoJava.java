package workbench.generics.l06.demo;

import java.util.Arrays;

/**
 * Java twin of ArrayCopyDemo.kt. Java arrays are covariant, so a Fruit[] parameter already accepts an
 * Apple[]. There is no wildcard for arrays. The price: the JVM checks every store at run time.
 * Fruit, Apple and Lemon are the Kotlin types from ArrayCopyDemo.kt.
 */
public class ArrayCopyDemoJava {

    static void copyRow(Fruit[] from, Fruit[] to) {
        for (int i = 0; i < from.length; i++) to[i] = from[i];   // each store is checked by the JVM
    }

    public static void main(String[] args) {
        Apple[] apples = {new Apple("Gala", 180), new Apple("Fuji", 150)};
        Fruit[] window = {new Lemon("Eureka", 120), new Lemon("Eureka", 95)};
        copyRow(apples, window);
        System.out.println("window: " + Arrays.toString(window));

        try {
            copyRow(apples, new Lemon[2]);       // compiles: a Lemon[] is a Fruit[]
        } catch (ArrayStoreException e) {
            System.out.println("ArrayStoreException: " + e.getMessage());
        }
    }
}
