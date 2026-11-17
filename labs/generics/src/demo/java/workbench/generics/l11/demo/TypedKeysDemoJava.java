package workbench.generics.l11.demo;

import java.lang.reflect.ParameterizedType;
import java.lang.reflect.Type;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Java twin of TypedKeysDemo.kt. The key's type comes from a super type token; Java generics are invariant. */
public class TypedKeysDemoJava {

    static abstract class TypeRef<T> {
        final Type type = ((ParameterizedType) getClass().getGenericSuperclass()).getActualTypeArguments()[0];
    }

    record Key<T>(String name, Type type) {
        static <T> Key<T> of(String name, TypeRef<T> ref) { return new Key<>(name, ref.type); }
    }

    static final class Attributes {
        private final Map<Key<?>, Object> values = new HashMap<>();
        <T> void set(Key<T> key, T value) { values.put(key, value); }
        @SuppressWarnings("unchecked")                          // safe: only set(Key<T>, T) puts values in
        <T> T get(Key<T> key) { return (T) values.get(key); }
    }

    static final Key<List<String>> VARIETIES = Key.of("varieties", new TypeRef<List<String>>() {});
    static final Key<Integer> TOTAL = Key.of("total grams", new TypeRef<Integer>() {});

    public static void main(String[] args) {
        Attributes attrs = new Attributes();
        attrs.set(VARIETIES, List.of("Gala", "Fuji"));
        attrs.set(TOTAL, 330);
        List<String> varieties = attrs.get(VARIETIES);         // typed by the key: no cast here
        System.out.println("varieties = " + varieties + ", total = " + attrs.get(TOTAL) + " g");

        // Wrong move. Uncomment, predict the error, then run.
        // attrs.set(VARIETIES, 42);
    }
}
