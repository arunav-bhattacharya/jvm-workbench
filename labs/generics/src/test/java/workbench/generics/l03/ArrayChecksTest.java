package workbench.generics.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;

class ArrayChecksTest {

    @Test
    @DisplayName("canStore says no when the value does not fit the array's real element type")
    void canStoreRejectsWrongType() {
        Object[] looksLikeObjects = new String[1];          // compiles: arrays are covariant
        assertThat(ArrayChecks.canStore(looksLikeObjects, 42)).isFalse();
        assertThat(ArrayChecks.canStore(new Integer[1], 2.5)).isFalse();
    }

    @Test
    @DisplayName("canStore says yes for the element type, its subtypes and null")
    void canStoreAcceptsFittingValues() {
        assertThat(ArrayChecks.canStore(new String[1], "EUR")).isTrue();
        assertThat(ArrayChecks.canStore(new Number[1], 42)).isTrue();       // Integer is a Number
        assertThat(ArrayChecks.canStore(new Object[1], 42)).isTrue();
        assertThat(ArrayChecks.canStore(new String[1], null)).isTrue();
    }

    @Test
    @DisplayName("canStore agrees with what the JVM really does")
    void canStoreMatchesTheJvm() {
        Object[][] arrays = { new String[1], new Number[1], new Integer[1], new Object[1], new CharSequence[1] };
        Object[] values = { "EUR", 42, 2.5, new StringBuilder("x"), new Object() };
        for (Object[] array : arrays) {
            for (Object value : values) {
                boolean jvmSaysYes;
                try {
                    array[0] = value;
                    jvmSaysYes = true;
                } catch (ArrayStoreException e) {
                    jvmSaysYes = false;
                }
                assertThat(ArrayChecks.canStore(array, value))
                        .as("%s into %s", value.getClass().getSimpleName(), array.getClass().getSimpleName())
                        .isEqualTo(jvmSaysYes);
            }
        }
    }

    @Test
    @DisplayName("widenSafely returns a real Object[] that accepts any value")
    void widenSafelyMakesARealObjectArray() {
        String[] names = { "card", "sepa" };
        Object[] widened = ArrayChecks.widenSafely(names);
        assertThat(widened.getClass()).isEqualTo(Object[].class);
        assertThat(widened).containsExactly("card", "sepa");
        assertThatCode(() -> widened[0] = 42).doesNotThrowAnyException();
        assertThat(names[0]).isEqualTo("card");             // a copy: the original is untouched
    }
}
