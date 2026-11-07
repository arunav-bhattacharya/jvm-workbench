package workbench.modernjava.l02.demo;

import java.lang.reflect.Modifier;

/** A sealed interface names its direct subtypes, and the JVM keeps that list. */
public class SealedBasics {

    sealed interface Command permits Authorize, Capture, Refund {}

    record Authorize(String authCode, long amountMinor) implements Command {}   // records are final

    record Capture() implements Command {}

    record Refund(long amountMinor) implements Command {}

    // Step 2: uncomment this line and compile.
    // static final class Void implements Command {}

    public static void main(String[] args) {
        System.out.println("Command.isSealed():  " + Command.class.isSealed());
        for (Class<?> c : Command.class.getPermittedSubclasses()) {
            System.out.println("permits:             " + c.getSimpleName()
                    + (Modifier.isFinal(c.getModifiers()) ? " (final)" : ""));
        }
        System.out.println("Refund.isSealed():   " + Refund.class.isSealed());
    }
}
