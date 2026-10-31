package workbench.generics.l01.demo;

import java.util.ArrayList;
import java.util.List;

/** A raw type switches the checks off. The bad value goes in quietly and fails on the way out. */
public class RawTypeDemo {

    // "List" with no <...> is a raw type: javac stops checking what goes in
    static void legacyAppend(List ids) {
        ids.add(42);                                // compiles, with an unchecked warning
    }

    public static void main(String[] args) {
        List<String> ids = new ArrayList<>();       // diamond: javac infers ArrayList<String>
        ids.add("pay_1001");
        legacyAppend(ids);
        System.out.println("size = " + ids.size() + ", nothing failed yet");
        try {
            for (String id : ids) {                 // javac inserted a (String) cast here
                System.out.println(id.toUpperCase());
            }
        } catch (ClassCastException e) {
            System.out.println("ClassCastException: " + e.getMessage());
        }
    }
}
