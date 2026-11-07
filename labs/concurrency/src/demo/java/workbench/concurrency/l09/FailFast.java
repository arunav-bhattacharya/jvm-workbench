package workbench.concurrency.l09;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;

/** ConcurrentModificationException needs no second thread. And concurrent collections never throw it. */
public class FailFast {
    public static void main(String[] args) {
        // 1. one thread, an ArrayList, a remove inside for-each
        List<String> pending = new ArrayList<>(List.of("pay-1", "pay-2", "pay-3", "pay-4"));
        try {
            for (String p : pending) {
                if (p.equals("pay-2")) pending.remove(p);   // changes the list under its own iterator
            }
        } catch (RuntimeException e) {
            System.out.println("ArrayList, one thread:      " + e.getClass().getSimpleName());
        }

        // 2. the same with a ConcurrentHashMap: weakly consistent, never throws
        Map<String, Integer> open = new ConcurrentHashMap<>(Map.of("pay-1", 1, "pay-2", 2, "pay-3", 3, "pay-4", 4));
        for (String k : open.keySet()) {
            if (k.equals("pay-2")) open.remove(k);
            if (k.equals("pay-3")) open.put("pay-5", 5);       // may or may not show up in this loop
        }
        System.out.println("ConcurrentHashMap:          no exception, now " + open.size() + " keys");

        // 3. CopyOnWriteArrayList: the loop walks a snapshot taken when it started
        List<String> hooks = new CopyOnWriteArrayList<>(List.of("a", "b", "c"));
        int seen = 0;
        for (String h : hooks) {
            hooks.add(h + "+");                                // goes into a NEW array
            seen++;
        }
        System.out.println("CopyOnWriteArrayList:       loop saw " + seen + " items, list now has " + hooks.size());

        // 4. the single-thread fix for case 1: remove through the iterator, or removeIf
        pending = new ArrayList<>(List.of("pay-1", "pay-2", "pay-3", "pay-4"));
        pending.removeIf(p -> p.equals("pay-2"));
        System.out.println("ArrayList.removeIf:         " + pending);
    }
}
