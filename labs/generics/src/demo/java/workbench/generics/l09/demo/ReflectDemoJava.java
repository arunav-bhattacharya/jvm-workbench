package workbench.generics.l09.demo;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Arrays;

/**
 * Java twin of ReflectDemo.kt. Java reflection needs no extra jar: it answers Java-level questions
 * (fields, methods) about Kotlin classes too. It doesn't know Kotlin ideas like data classes.
 */
public class ReflectDemoJava {
    public static void main(String[] args) throws Exception {
        System.out.println("fields:  " + Arrays.stream(Apple.class.getDeclaredFields()).map(Field::getName).sorted().toList());
        System.out.println("methods: " + Arrays.stream(Apple.class.getDeclaredMethods()).map(Method::getName).sorted().toList());
        // A Kotlin object is a class with a static INSTANCE field: Java's way to get objectInstance.
        System.out.println("Storeroom.INSTANCE: " + Storeroom.class.getField("INSTANCE").get(null).getClass().getSimpleName());
        System.out.println("is it a data class? Java reflection can't say: it has no such idea.");
    }
}
