package workbench.generics.l09.demo;

import java.lang.reflect.ParameterizedType;
import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;

/**
 * Java twin of ClassVsTypeDemo.kt. Java has Class but no KType. The closest thing is
 * java.lang.reflect.Type, which you can read from a declaration (here, a field).
 */
public class ClassVsTypeDemoJava {

    static List<String> ids = List.of("pay_1");     // a declaration keeps its generic type

    public static void main(String[] args) throws Exception {
        Class<String> c = String.class;
        Type t = ClassVsTypeDemoJava.class.getDeclaredField("ids").getGenericType();
        System.out.println("Class: " + c);
        System.out.println("Type:  " + t + " (read from the field declaration)");

        System.out.println("ArrayList<String> and ArrayList<Integer> share a class: "
            + (new ArrayList<String>().getClass() == new ArrayList<Integer>().getClass()));
        System.out.println("the field's Type keeps its argument: " + ((ParameterizedType) t).getActualTypeArguments()[0]);
        // Java types carry no nullability, so there is no twin of typeOf<String?>().
    }
}
