package workbench.modernjava.l01;

import java.util.Locale;
import java.util.Objects;
import java.util.regex.Pattern;

public record Money(long minor, String currency) {
    private static final Pattern ISO = Pattern.compile("[A-Z]{3}");   // static fields are allowed

    // compact canonical constructor: every Money ever built passes through here,
    // whether it came from new, a factory, a wither or deserialization
    public Money {
        Objects.requireNonNull(currency, "currency");
        currency = currency.trim().toUpperCase(Locale.ROOT);   // reassign the parameter, not this.currency
        if (!ISO.matcher(currency).matches()) {
            throw new IllegalArgumentException("currency must be three letters: " + currency);
        }
        if (minor < 0) {
            throw new IllegalArgumentException("negative amount: " + minor);
        }
    }   // the compiler assigns this.minor and this.currency here, after the body

    public Money plus(Money other) {
        if (!currency.equals(other.currency)) {
            throw new IllegalArgumentException("currency mismatch: " + currency + " + " + other.currency);
        }
        return new Money(Math.addExact(minor, other.minor), currency);   // goes through the checks again
    }
}
