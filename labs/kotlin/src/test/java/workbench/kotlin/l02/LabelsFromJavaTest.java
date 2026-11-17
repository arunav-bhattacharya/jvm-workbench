package workbench.kotlin.l02;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class LabelsFromJavaTest {

    @Test
    @DisplayName("Java calls parseWeight and gets the raw grams as a long: Weight does not exist at run time here")
    void javaSeesALong() {
        long grams = LabelsKt.parseWeight("1.25");        // the Kotlin return type Weight is a long for Java
        assertThat(grams).isEqualTo(1_250L);
        assertThatThrownBy(() -> LabelsKt.parseWeight("-1.0"))
                .isInstanceOf(IllegalArgumentException.class);   // validation ran inside Kotlin
    }
}
