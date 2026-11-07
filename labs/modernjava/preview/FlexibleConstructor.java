// Needs JDK 25 or newer: flexible constructor bodies are final in JDK 25.
// On JDK 21 javac rejects it with "constructor is not canonical, so its first statement
// must invoke another constructor".
// Run from labs/modernjava:   java preview/FlexibleConstructor.java

import java.util.Locale;
import java.util.Objects;

public class FlexibleConstructor {

    record Money(long minor, String currency) {
        Money {
            Objects.requireNonNull(currency, "currency");
            if (minor < 0) throw new IllegalArgumentException("negative amount: " + minor);
            currency = currency.toUpperCase(Locale.ROOT);
        }

        // parse "12.50 EUR": statements before this(...) are allowed from JDK 25
        Money(String text) {
            String[] parts = text.trim().split(" ");
            if (parts.length != 2) throw new IllegalArgumentException("expected '<amount> <currency>': " + text);
            long minor = new java.math.BigDecimal(parts[0]).movePointRight(2).longValueExact();
            this(minor, parts[1]);
        }
    }

    public static void main(String[] args) {
        System.out.println(new Money("12.50 eur"));
        try {
            new Money("12.50");
        } catch (IllegalArgumentException e) {
            System.out.println("IAE: " + e.getMessage());
        }
    }
}
