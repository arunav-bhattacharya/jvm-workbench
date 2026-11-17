package workbench.modernjava.l01;

import java.util.Locale;
import java.util.Objects;
import java.util.regex.Pattern;

public record Shelfmark(String section, int shelf) {
    private static final Pattern SECTION = Pattern.compile("[A-Z]{3}");   // static fields are allowed

    // compact canonical constructor: every Shelfmark ever built passes through here,
    // whether it came from new, a factory, a wither or deserialization
    public Shelfmark {
        Objects.requireNonNull(section, "section");
        section = section.trim().toUpperCase(Locale.ROOT);   // reassign the parameter, not this.section
        if (!SECTION.matcher(section).matches()) {
            throw new IllegalArgumentException("section must be three letters: " + section);
        }
        if (shelf < 1 || shelf > 999) {
            throw new IllegalArgumentException("shelf must be 1 to 999: " + shelf);
        }
    }   // the compiler assigns this.section and this.shelf here, after the body

    public Shelfmark next() {
        return new Shelfmark(section, shelf + 1);   // goes through the checks again: 999 has no next
    }
}
