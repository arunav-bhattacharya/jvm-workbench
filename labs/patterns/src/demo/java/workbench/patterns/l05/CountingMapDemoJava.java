package workbench.patterns.l05;

import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;

/**
 * The Java twin of CountingMapDemo.kt. Java has no `by`, so the short way is inheritance,
 * and then the result depends on how the parent class happens to be written.
 */
public class CountingMapDemoJava {

    static final class CountingMap<K, V> extends HashMap<K, V> {
        int puts;
        @Override public V put(K key, V value) {
            puts++;
            return super.put(key, value);
        }
    }

    // Effective Java item 18: HashSet.addAll calls add for each element, so this counts twice
    static final class CountingSet<E> extends HashSet<E> {
        int added;
        @Override public boolean add(E e) {
            added++;
            return super.add(e);
        }
        @Override public boolean addAll(Collection<? extends E> c) {
            added += c.size();
            return super.addAll(c);
        }
    }

    public static void main(String[] args) {
        CountingMap<String, Integer> m = new CountingMap<>();
        m.put("a", 1);
        m.putAll(Map.of("b", 2, "c", 3));      // HashMap.putAll doesn't call put, today
        System.out.println("CountingMap: puts=" + m.puts + ", size=" + m.size());

        CountingSet<String> s = new CountingSet<>();
        s.addAll(List.of("x", "y", "z"));
        System.out.println("CountingSet: added=" + s.added + ", size=" + s.size());
    }
}
