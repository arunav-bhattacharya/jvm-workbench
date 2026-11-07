package workbench.kotlin.l02;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ReceiptsFromJavaTest {

    @Test
    @DisplayName("Java calls parseAmount and gets the raw cents as a long: Money does not exist at run time here")
    void javaSeesALong() {
        long cents = ReceiptsKt.parseAmount("19.99");     // the Kotlin return type Money is a long for Java
        assertThat(cents).isEqualTo(1_999L);
        assertThatThrownBy(() -> ReceiptsKt.parseAmount("-1.00"))
                .isInstanceOf(IllegalArgumentException.class);   // validation ran inside Kotlin
    }
}
