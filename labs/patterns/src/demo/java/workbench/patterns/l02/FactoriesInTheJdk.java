package workbench.patterns.l02;

import java.time.Duration;
import java.util.EnumSet;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Static factories in the JDK pick the class for you. Predict each class name before you run this. */
public class FactoriesInTheJdk {
    public static void main(String[] args) {
        // the factory picks an implementation based on the input
        System.out.println("List.of(1)            -> " + List.of(1).getClass().getSimpleName());
        System.out.println("List.of(1, 2, 3)      -> " + List.of(1, 2, 3).getClass().getSimpleName());
        System.out.println("EnumSet of TimeUnit   -> " + EnumSet.noneOf(TimeUnit.class).getClass().getSimpleName()
                + " (" + TimeUnit.values().length + " constants)");
        System.out.println("EnumSet of scripts    -> " + EnumSet.noneOf(Character.UnicodeScript.class).getClass().getSimpleName()
                + " (" + Character.UnicodeScript.values().length + " constants)");

        // the factory can hand back a cached instance instead of a new one
        System.out.println("valueOf(100) twice    -> same object? " + (Integer.valueOf(100) == Integer.valueOf(100)));
        System.out.println("Duration.ofSeconds(0) -> same as ZERO? " + (Duration.ofSeconds(0) == Duration.ZERO));

        // and its name says what you get, which a constructor can't
        System.out.println("Duration.ofMinutes(2) -> " + Duration.ofMinutes(2));
    }
}
