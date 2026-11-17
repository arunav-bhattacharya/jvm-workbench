package workbench.functional.l06.demo;

import java.util.function.Consumer;

/** Java equivalent: a Java lambda can't assign a local variable at all, so the assignment is a plain statement. */
public class ValInitJava {
    record Jar(String label, int grams) {}

    static Jar fillJar(int grams) { return new Jar("J-" + grams % 97, grams); }

    public static void main(String[] args) {
        final String label1;
        Jar jar1 = fillJar(450);
        label1 = jar1.label();                                  // a statement, outside any lambda
        System.out.println("statement:    " + label1 + " for " + jar1.grams() + " g");

        // Uncomment the next two lines and run again. javac rejects any assignment to a local inside a lambda.
        // String label3;
        // Consumer<Jar> keep = j -> label3 = j.label();
    }
}
