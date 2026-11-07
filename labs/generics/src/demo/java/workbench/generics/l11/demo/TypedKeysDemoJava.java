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

    static final Key<List<String>> CURRENCIES = Key.of("currencies", new TypeRef<List<String>>() {});
    static final Key<Integer> RETRIES = Key.of("retries", new TypeRef<Integer>() {});

    public static void main(String[] args) {
        Attributes attrs = new Attributes();
        attrs.set(CURRENCIES, List.of("EUR", "USD"));
        attrs.set(RETRIES, 3);
        List<String> currencies = attrs.get(CURRENCIES);       // typed by the key: no cast here
        System.out.println("currencies = " + currencies + ", retries = " + attrs.get(RETRIES));

        // Wrong move. Uncomment, predict the error, then run.
        // attrs.set(CURRENCIES, 42);
    }
}
