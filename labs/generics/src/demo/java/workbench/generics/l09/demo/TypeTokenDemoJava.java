package workbench.generics.l09.demo;

import java.lang.reflect.ParameterizedType;
import java.lang.reflect.Type;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

/** Java twin of TypeTokenDemo.kt: the super type token, the trick behind Jackson's TypeReference. */
public class TypeTokenDemoJava {

    static abstract class TypeRef<T> {
        final Type type;

        protected TypeRef() {
            // getClass() is the anonymous subclass; its generic superclass is TypeRef<the type you wrote>
            type = ((ParameterizedType) getClass().getGenericSuperclass()).getActualTypeArguments()[0];
        }
    }

    // the well-known hole: inside a generic method, the token captures the type VARIABLE
    static <T> Type listOf() { return new TypeRef<List<T>>() {}.type; }

    public static void main(String[] args) {
        Type t = new TypeRef<Map<String, List<Integer>>>() {}.type;
        System.out.println("super type token: " + t);
        System.out.println("arguments:        " + Arrays.toString(((ParameterizedType) t).getActualTypeArguments()));
        System.out.println("inside a generic method: " + TypeTokenDemoJava.<String>listOf());

        // Wrong move. Uncomment, predict the error, then run.
        // Type k = new TypeRef<String>().type;
    }
}
