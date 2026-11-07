package workbench.kotlin.l02.demo;

import java.util.List;

/**
 * Java twin of BoxingDemo.kt. Java has the same split for long and Long: a primitive where it can,
 * a box when the value is used as a generic type, a nullable, or Object. Kotlin forbids === on
 * value classes; Java lets you compare boxes by identity, and it goes wrong above 127.
 */
public class BoxingDemoJava {

    static Object asGeneric(Object x) { return x; }

    public static void main(String[] args) {
        long minor = 1_999;
        Object boxed = asGeneric(minor);                 // autoboxed to Long
        System.out.println("as Object:   " + boxed.getClass().getSimpleName());
        System.out.println("in a list:   " + List.of(minor).get(0).getClass().getSimpleName());

        Long a = 1_999L, b = 1_999L;
        System.out.println("a == b (identity):  " + (a == b));         // two different Long objects
        System.out.println("a.equals(b):        " + a.equals(b));
        Long small1 = 100L, small2 = 100L;
        System.out.println("100L == 100L:       " + (small1 == small2)); // cached box, so true
    }
}
