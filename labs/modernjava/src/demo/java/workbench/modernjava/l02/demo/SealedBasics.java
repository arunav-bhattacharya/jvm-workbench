package workbench.modernjava.l02.demo;

import java.lang.reflect.Modifier;

/** A sealed interface names its direct subtypes, and the JVM keeps that list. */
public class SealedBasics {

    // the three things a member can ask for at the desk
    sealed interface Request permits Borrow, Renew, Return {}

    record Borrow(String isbn, int days) implements Request {}   // records are final

    record Renew(int extraDays) implements Request {}

    record Return() implements Request {}

    // Step 2: uncomment this line and compile.
    // static final class Donate implements Request {}

    public static void main(String[] args) {
        System.out.println("Request.isSealed(): " + Request.class.isSealed());
        for (Class<?> c : Request.class.getPermittedSubclasses()) {
            System.out.println("permits:            " + c.getSimpleName()
                    + (Modifier.isFinal(c.getModifiers()) ? " (final)" : ""));
        }
        System.out.println("Renew.isSealed():   " + Renew.class.isSealed());
    }
}
