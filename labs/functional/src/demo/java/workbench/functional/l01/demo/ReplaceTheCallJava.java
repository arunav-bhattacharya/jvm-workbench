package workbench.functional.l01.demo;

import java.util.List;

/** Java twin of ReplaceTheCall.kt: swapping a call for its value is safe only when the call is pure. */
public class ReplaceTheCallJava {

    // Pure: the result depends only on the argument, and calling it changes nothing.
    static int batterGrams(int pancakes) {
        return pancakes * 55;
    }

    // Impure: taking an egg out of the fridge is the whole point of the call. This fake fridge counts them.
    static int taken = 0;

    static String takeEgg() {
        taken++;
        return "egg_" + taken;
    }

    public static void main(String[] args) {
        // 1. With a pure function, a call and its value are interchangeable.
        int b = batterGrams(8);
        System.out.println("batterGrams(8) + batterGrams(8) = " + (batterGrams(8) + batterGrams(8)));
        System.out.println("int b = batterGrams(8); b + b   = " + (b + b));

        // 2. The same "harmless" refactoring on an impure call changes what the program does.
        String e = takeEgg();
        System.out.println("String e = takeEgg(); List.of(e, e) -> " + List.of(e, e) + ", eggs taken: " + taken);

        taken = 0;
        List<String> both = List.of(takeEgg(), takeEgg());
        System.out.println("List.of(takeEgg(), takeEgg())       -> " + both + ", eggs taken: " + taken);
    }
}
