// Needs JDK 25 or newer: flexible constructor bodies are final in JDK 25.
// On JDK 21 javac rejects it with "constructor is not canonical, so its first statement
// must invoke another constructor".
// Run from labs/modernjava:   java preview/FlexibleConstructor.java

import java.util.Locale;
import java.util.Objects;

public class FlexibleConstructor {

    record Shelfmark(String section, int shelf) {
        Shelfmark {
            Objects.requireNonNull(section, "section");
            if (shelf < 1) throw new IllegalArgumentException("shelf must be 1 or more: " + shelf);
            section = section.toUpperCase(Locale.ROOT);
        }

        // read a spine label such as "fic 12": statements before this(...) are allowed from JDK 25
        Shelfmark(String label) {
            String[] parts = label.trim().split(" ");
            if (parts.length != 2) throw new IllegalArgumentException("expected '<section> <shelf>': " + label);
            int shelf = Integer.parseInt(parts[1]);
            this(parts[0], shelf);
        }
    }

    public static void main(String[] args) {
        System.out.println(new Shelfmark("fic 12"));
        try {
            new Shelfmark("fic");
        } catch (IllegalArgumentException e) {
            System.out.println("IAE: " + e.getMessage());
        }
    }
}
