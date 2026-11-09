package workbench.functional.l08;

import java.util.ArrayList;
import java.util.List;

/**
 * Java equivalent: the JDK has no persistent collections. A new version means copying the old one
 * (O(n) per change) into an unmodifiable list. Structure sharing needs a library.
 */
public class PersistentJava {
    static List<String> adding(List<String> list, String element) {
        List<String> copy = new ArrayList<>(list);   // copies every element
        copy.add(element);
        return List.copyOf(copy);
    }

    public static void main(String[] args) {
        List<String> v1 = List.of("opening");
        List<String> v2 = adding(v1, "payout:m-acme");
        List<String> v3 = adding(adding(v2, "fee-income"), "payout:m-globex");
        System.out.println("v1 = " + v1);
        System.out.println("v2 = " + v2);
        System.out.println("v3 = " + v3);

        List<String> builder = new ArrayList<>(v3);  // several changes: copy once, change, freeze
        builder.remove(0);
        builder.add("closing");
        List<String> v4 = List.copyOf(builder);
        System.out.println("v4 = " + v4);
        System.out.println("v3 = " + v3 + " (unchanged)");
    }
}
