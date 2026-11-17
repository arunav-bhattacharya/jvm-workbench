package workbench.generics.l08;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class ParsersFromJavaTest {

    @Test
    @DisplayName("Java registers and parses with Class tokens: Weight.class is the type argument")
    void javaUsesClassTokens() {
        Parsers parsers = new Parsers();
        parsers.register(Weight.class, Weight::parse);
        Weight w = parsers.parse("0.18 kg", Weight.class);
        assertThat(w).isEqualTo(new Weight(180));
        // parsers.<Weight>parse("0.18 kg") would not compile here: Java can't call a reified function
    }
}
