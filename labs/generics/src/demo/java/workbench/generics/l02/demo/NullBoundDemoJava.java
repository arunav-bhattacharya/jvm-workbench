package workbench.generics.l02.demo;

import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

/** Java twin of NullBoundDemo.kt. Java has no T : Any, so null stays ambiguous unless you check at run time. */
public class NullBoundDemoJava {

    static class Cache<K, V> {
        private final Map<K, V> entries = new HashMap<>();
        void put(K key, V value) { entries.put(key, value); }       // HashMap accepts null values
        V get(K key) { return entries.get(key); }                   // null: absent, or a stored null?
    }

    public static void main(String[] args) {
        Cache<String, String> problems = new Cache<>();
        problems.put("apples", null);          // "we checked the apples: no problem"

        System.out.println("apples -> " + problems.get("apples"));   // stored null
        System.out.println("figs -> " + problems.get("figs"));       // never checked
        System.out.println("Can you tell those two apart? Neither can the caller.");

        // Java's closest fix is a run-time check. Uncomment, run, and see where it fails.
        // Objects.requireNonNull(null, "stored values must not be null");
    }
}
