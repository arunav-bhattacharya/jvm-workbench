package workbench.generics.l08;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class ParsersFromJavaTest {

    @Test
    @DisplayName("Java registers and parses with Class tokens: Money.class is the type argument")
    void javaUsesClassTokens() {
        Parsers parsers = new Parsers();
        parsers.register(Money.class, Money::parse);
        Money m = parsers.parse("99.90 USD", Money.class);
        assertThat(m).isEqualTo(new Money(9_990, "USD"));
        // parsers.<Money>parse("99.90 USD") would not compile here: Java can't call a reified function
    }
}
