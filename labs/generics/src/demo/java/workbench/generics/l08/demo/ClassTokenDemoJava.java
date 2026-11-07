package workbench.generics.l08.demo;

import java.math.BigDecimal;
import java.util.Currency;

/**
 * Java twin of ClassTokenDemo.kt. It calls the Kotlin functions in ClassTokenDemo.kt directly:
 * the Class-token version works from Java, the reified one does not exist for javac.
 */
public class ClassTokenDemoJava {
    public static void main(String[] args) {
        BigDecimal zero = ClassTokenDemoKt.defaultOf(BigDecimal.class);
        Currency eur = ClassTokenDemoKt.defaultOf(Currency.class);
        String blank = ClassTokenDemoKt.defaultOf(String.class);
        System.out.println("zero = " + zero + ", eur = " + eur + ", blank = '" + blank + "'");

        // Java has the same primitive trap: int.class and Integer.class are different Class objects.
        System.out.println("int.class = " + int.class + ", Integer.class = " + Integer.class);

        // Wrong move. Uncomment, predict the error, then run.
        // BigDecimal viaReified = ClassTokenDemoKt.<BigDecimal>defaultOf();
    }
}
