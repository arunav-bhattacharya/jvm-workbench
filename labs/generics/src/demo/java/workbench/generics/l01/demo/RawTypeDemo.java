package workbench.generics.l01.demo;

import java.util.ArrayList;
import java.util.List;

/** A raw type switches the checks off. The bad value goes in quietly and fails on the way out. */
public class RawTypeDemo {

    // an old helper, written as if Java had no generics: "List" with no <...> is a raw type
    static void addOldStock(List names) {
        names.add(42);                              // compiles, with an unchecked warning
    }

    public static void main(String[] args) {
        List<String> varieties = new ArrayList<>(); // diamond: javac infers ArrayList<String>
        varieties.add("Gala");
        addOldStock(varieties);
        System.out.println("size = " + varieties.size() + ", nothing failed yet");
        try {
            for (String variety : varieties) {      // javac inserted a (String) cast here
                System.out.println(variety.toUpperCase());
            }
        } catch (ClassCastException e) {
            System.out.println("ClassCastException: " + e.getMessage());
        }
    }
}
